# -*- coding: UTF-8 -*-
#Native
import json

#Django
from django.db import models
from django.db import connection

#Proyect
from lib.stop_words.functions import remove_non_unicode
from lib.stop_words.functions import remove_spaces
from lib.stop_words.functions import remove_non_alphanumeric
from lib.stop_words.functions import remove_words
from lib.parser.functions import strip_tags

class Client(models.Model):
    name = models.CharField(max_length = 255, unique = True)
    
    def __unicode__(self):
        return self.name

class DataSet(models.Model):
    """ Represents a dataSet """
    
    name = models.CharField(max_length = 30)
    url = models.CharField(max_length = 50)
    #Usado para el parser para leer los titulos de los post en el home del sitio
    home_pattern = models.CharField(max_length = 50)
    #Usado por el parser para leer el contenido en la pagina de un articulo
    content_pattern = models.CharField(max_length = 100)
    #Asumiendo que el sitio es un blog, Numero de post por pagina.
    post_per_page = models.IntegerField(default = "0")
    
    def __unicode__(self):
        return self.name    

class LdaModel(models.Model):
    """ Represents a LdaModel """

    #Solo representa un label para el modelo
    name = models.CharField(max_length = 255)
    #Soporte Stemming
    stemming = models.NullBooleanField()

    alpha = models.FloatField(null=True)
    beta = models.FloatField(null=True)
    n_topics = models.IntegerField(null=True)
    
    def removeReferences(self):
        """ Removes all elements related to the model """        
        cursor = connection.cursor()
        
        #Obtengo los ids de los topics del modelo y los dejo en un string del tipo 1,2,3,4,5
        topics = Topic.objects.filter(ldamodel = self)
        topics_str_list = ','.join([str(topic.id) for topic in topics])
        
        #Reviso si habian topics relacionados al modelo
        if topics_str_list:
            cursor.execute("DELETE FROM classifier_classifiernode WHERE topic_id IN ("+topics_str_list+")")
            cursor.execute("DELETE FROM validation_docsegtop WHERE topic_id IN ("+topics_str_list+")")
            cursor.execute("DELETE FROM validation_countdocsegtop WHERE topic_id IN ("+topics_str_list+")")
            cursor.execute("DELETE FROM validation_sample WHERE topic_id IN ("+topics_str_list+")")
            cursor.execute("DELETE FROM application_topicword WHERE topic_id IN ("+topics_str_list+")")
            cursor.execute("DELETE FROM application_documenttopic WHERE topic_id IN ("+topics_str_list+")")
            cursor.execute("DELETE FROM application_topic WHERE id IN ("+topics_str_list+")")
        
        cursor.execute("DELETE FROM application_wordldamodel WHERE ldamodel_id = "+str(self.id))
        cursor.execute("DELETE FROM classifier_classifiernode WHERE ldamodel_id = "+str(self.id))
        
    def __unicode__(self):
        return self.name

class DataSetLdaModel(models.Model):
    """ Relational model between DataSet and LdaModel """
    dataset = models.ForeignKey(DataSet)
    ldamodel = models.ForeignKey(LdaModel)
    #El sitio puede estar deshabilitado para un cierto modelo, este campo controla eso:
    enabled = models.BooleanField()

    def __unicode__(self):
        return self.ldamodel.name+" - "+self.dataset.name

class Word(models.Model):
    """ Represents a Word on the system. Come from documents. """
    
    #La palabra en si misma
    name = models.CharField(max_length=200,db_index=True, unique = True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def lev_distance(self,b):
        """ Calculates Levenstein distance between self and b word """
        str1 = self.name
        str2 = b.name
        d=dict()
        for i in range(len(str1)+1):
            d[i]=dict()
            d[i][0]=i
        for i in range(len(str2)+1):
            d[0][i] = i
        for i in range(1, len(str1)+1):
            for j in range(1, len(str2)+1):
                d[i][j] = min(d[i][j-1]+1, d[i-1][j]+1, d[i-1][j-1]+(not str1[i-1] == str2[j-1]))
        return d[len(str1)][len(str2)]

    def max_prefix(self,b):
        """ Gets the longest common prefix between b and self """
        word1 = self.name
        word2 = b.name
        index = 1
        if (len(word1) or len(word2)) < 1:
            return 0
        while index <= len(word1):
            if word1[0:index] != word2[0:index]:
                return index
            index += 1
        return index
    
    def gl_distance(self,b):
        """ Calculates GL distance between self and b """
        mp = self.max_prefix(b)
        return float(min(len(self.name),len(b.name))*self.lev_distance(b))/float(mp*mp)

class Document(models.Model):
    """ Represents certain text comming from a Post froma Blog """

    #Titulo del articulo
    title = models.CharField(max_length = 300)
    #Url del articulo
    url = models.CharField(max_length = 200, default = '', null = True)
    #Sitio del que proviene
    dataset = models.ForeignKey(DataSet, default = "0")
    #Id externo
    external_id = models.IntegerField(null = True)
    #Resultado de clasificación
    prediction = models.TextField(null = True)

    #Numero de comentarios en caso de existir
    comments = models.IntegerField(null = True) #Not used
    
    #True indica que el documento no se tomara para entrenamiento, solo para validacion
    test = models.BooleanField()

    #Numero de palabras en el documento despues de limpieza
    n_words = models.IntegerField(default = "0")
    #Palabras en el documento que no son consideradas en el diccionario
    not_in_dic = models.IntegerField(default = "0")
    #Palabras que existen en el diccionario pero cuyo peso es muy bajo para ser tomados en cuenta
    low_weight_words = models.IntegerField(default = "0")

    #Texto original
    original_content = models.TextField(null = True)
    #original_content despues de la fase transform de limpieza 
    cleaned_content = models.TextField(null = True)
    #cleaned_content despues de la fase de stemming
    steamed_content = models.TextField(null = True)
    
    #La frecuencia de la palabra con mayor frecuencia en el documento
    max_word_frec = models.IntegerField(null=True)
    #True indica si las palabras de este documento ya estan en el diccionario
    loaded_words = models.BooleanField(default = "0")
    frec_calculated = models.BooleanField(default = "0")

    def __unicode__(self):
        return self.title

    def get_original(self):
        return self.original_content.split(' ')

    def clean_content(self,stopwords = None, s_t = True):
        if not self.cleaned_content:
            aux = unicode(self.original_content)

            #Quito <>,[], <!-- --> y saltos de linea
            if s_t:
                aux = strip_tags(aux)

            #quito espacios en bordes, llevo a lowercase y saco tildes
            aux = ' '+remove_non_unicode(aux.strip().lower())+' '

            #quito Numeros y Caracteres
            aux = remove_non_alphanumeric(aux)

            #quito espacios
            aux = remove_spaces(aux)

            #quito Stop Words
            if stopwords is None:
                sw = Stopword.objects.all()
                stopwords = '|'.join([" "+str(x)+" " for x in sw])

            if stopwords:
                aux = remove_words(aux,stopwords)
            else:
                print "Document %s: There aren't any stop words!" % self.id

            aux = aux.replace('  ',' ')

            self.cleaned_content = aux.strip()

class DocumentDistribution(models.Model):

    document = models.ForeignKey(Document)
    ldamodel = models.ForeignKey(LdaModel)
    
    #Representa la distribucion de palabras del texto, debe estar definido antes de la fase de training
    #Ejemplo: [1,1,2,3,4,5,6,6,22], cada numero es un id de una palabra en hexadecimal
    distribution = models.TextField()    

    def __unicode__(self):
        return self.distribution

class Frequency(models.Model): #
    """ Stores the frequency of a word over a certain document """
        
    document = models.ForeignKey(Document)
    word = models.ForeignKey(Word)
    #Number of times a word appears in a document
    frequency = models.IntegerField()

    def __unicode__(self):
        return str(self.document.id)+":"+str(self.word.id)+" = "+str(self.frequency)

class WordDataSetFrequency(models.Model):
    """ Stores the frequency of a word over a given DataSet """

    word = models.ForeignKey(Word)
    dataset = models.ForeignKey(DataSet)
    # Numbre of times the word appears into the dataset
    frequency = models.IntegerField()

class Stopword(models.Model):
    """ Stores the set of stopwords """

    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name

class WordLdaModel(models.Model):
    """ Stores the frequency data for a word over a given set of datasets asociated to a LdaModel """
    word = models.ForeignKey(Word)
    ldamodel = models.ForeignKey(LdaModel)
    #Number of document the word appears in, on a LdaModel
    n_doc_appearances = models.IntegerField()
    #Number of times the word appears into a set of documents from a LdaModel
    frequency = models.IntegerField()
    
    def __unicode__(self):
        return str(self.word.name)+"frequency distribution"

class Topic(models.Model):

    ldamodel = models.ForeignKey(LdaModel)
    #Label for the topic
    label = models.CharField(max_length=200)
    #Score for a topic, more score, more relevant
    score = models.FloatField(null = True)
    #If this topic is active or not
    active = models.BooleanField(default=1)
    #String like this "{'Belelu':'30%','Ferplei':'70%'}"
    #The names come from the dataset asociated to the LdaModel
    dataset_relevance = models.TextField()
    #Most Relevant Dataset
    #dataset_related = models.ForeignKey(DataSet, null = True)

    def __unicode__(self):
        return self.ldamodel.name+":"+self.label

    def get_words(self,limit = 50):
        """ Return the list of the more representative words for the topic """
        if limit:
            return Topicword.objects.filter(topic__exact=self).order_by('-value')[0:limit]
        else:
            return Topicword.objects.filter(topic__exact=self).order_by('-value')
            
    def get_documents(self,limit = 50):
        """ Return the list of the more representative documents for the topic """
        if limit:
            return Documenttopic.objects.filter(topic__exact=self).order_by('-value')[0:limit]
        else:
            return Documenttopic.objects.filter(topic__exact=self).order_by('-value')

    def get_dataset_relevance(self):

        total = float(0)
        aux = {}

        cursor = connection.cursor()
        cursor.execute("SELECT SUM(td.value) as suma, s.name,s.id FROM application_documenttopic td JOIN application_document d ON td.document_id = d.id JOIN application_dataset s ON s.id = d.dataset_id  WHERE td.topic_id = "+str(self.id)+" GROUP BY td.topic_id, s.id ORDER BY `td`.`topic_id` ASC ")
        rows = cursor.fetchall()
        
        for row in rows:
            aux[row[2]] = (row[1],row[0])
            total += row[0]

        result = [{"id":"%d" % a,"name":aux[a][0],"value":"%.4f" % round(aux[a][1],4),"percent":"%.2f" % round(100*aux[a][1]/float(total),2)} for a in aux]
        
        return result

    def tpl_dataset_relevance(self):
        return json.loads(self.dataset_relevance.replace("'",'"').replace(' u"',' "'))

    def get_points(self):
        cursor = connection.cursor()
        cursor.execute("SELECT SUM(td.value) as suma FROM application_documenttopic td WHERE td.topic_id = "+str(self.id)+" GROUP BY td.topic_id ")
        row = cursor.fetchone()
        return json.dumps(row[0])

    def get_percent_of_documents_related(self):
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*)/B.total  FROM application_documenttopic A JOIN (SELECT COUNT(*) as total, topic_id FROM application_documenttopic WHERE topic_id = "+str(self.id)+") B ON A.topic_id = B.topic_id  WHERE A.value > 0.15 AND A.topic_id = "+str(self.id))
        row = cursor.fetchone()
        return row[0]*100

    def get_related_dataset(self):
        cursor = connection.cursor()
        sql = "SELECT SUM(td.value) as suma, s.id FROM application_documenttopic td JOIN application_document d ON td.document_id = d.id JOIN application_dataset s ON s.id = d.dataset_id  WHERE td.topic_id = "+str(self.id)+" GROUP BY td.topic_id, s.id ORDER BY suma DESC LIMIT 0,1"
        cursor.execute(sql)
        return cursor.fetchone()[1]

class Topicword(models.Model):
    """ Stores the association between a topic and a word """
    
    topic = models.ForeignKey(Topic)
    word = models.ForeignKey(Word)
    value = models.FloatField()

    def word_name(self):
        return self.word.name
        
    def topic_label(self):
        return self.topic.label

    def __unicode__(self):
        return self.word.name

class Documenttopic(models.Model):
    """ Stores the association between a topic and a document """

    document = models.ForeignKey(Document)
    topic = models.ForeignKey(Topic)
    value = models.FloatField()

    def __unicode__(self):
        return self.document.title

