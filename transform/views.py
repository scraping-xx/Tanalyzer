# -*- coding: UTF-8 -*-
#Python
from os import environ, getcwd
from re import search

#Django
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connection
from django.conf import settings
from django.core.cache import get_cache, cache
from django.db.models import Q
stem_cache = get_cache('stemming')

#Proyect
from application.models import * #Change
from settings_local import *


#Proyect Libs
from lib.util.functions import unique
from lib.util.functions import avance
from lib.stop_words.functions import remove_words
from lib.stop_words.functions import remove_non_unicode
#from lib.API import libmorfo_python
FILE_SW = 'stopwords.txt'

def do(request,ldamodel_id = None):

    #clean_content(request)
    #return HttpResponse("Ok")

    #clean_steam()

    if not ldamodel_id:

        ldamodels = LdaModel.objects.all()
        load_words(request, ldamodel)
        get_freq(request,ldamodel)
        get_worddatasetfreq()

        for ldamodel in ldamodels:
            
            get_wordldamodel(request,ldamodel)
            clean_low_freq(5)
            remove_common_words(ldamodel)

    
        for ldamodel in ldamodels:
            set_distribution(ldamodel)

    else:

        ldamodel = LdaModel.objects.get(pk = ldamodel_id)

        load_words(request,ldamodel)
        get_freq(request,ldamodel)
        get_worddatasetfreq() 
               
        get_wordldamodel(request,ldamodel)
        clean_low_freq(5)
        remove_common_words(ldamodel)

        set_distribution(ldamodel)       

    return HttpResponse("Ok")


def clean_content(request):
    """Limpia el contenido de un documento filtrando stop words y caracteres que no son letras"""

    documents = Document.objects.filter(Q(cleaned_content='') | Q(cleaned_content=None)| Q(steamed_content='') | Q(steamed_content=None))

    goal = 0
    current = 0
    leng = len(documents)
    print " -> Removing Stop Words and weird chars..."

    sw = Stopword.objects.all()
    stopwords = '|'.join([" "+str(x)+" " for x in sw])

    print " -> Cleaning Documents"
    for d in documents:
        goal, current = avance(current, leng, goal)
        if not d.cleaned_content:
            d.clean_content(stopwords)
            if d.cleaned_content:
                #d.stemmed_content = freeling_stemming(d.cleaned_content)
                d.save()
            else:
                d.delete()

    print "  Documents cleaned!"

def clean_steam():

    documents = Document.objects.all()
    goal = 0
    current = 0
    leng = len(documents)
    for document in documents:
        goal, current = avance(current, leng, goal)
        if document.steamed_content:
            text_to_clean = document.steamed_content

            aux = unicode(text_to_clean)

            #Quito <>,[], <!-- --> y saltos de linea
            aux = strip_tags(aux)

            #quito espacios en bordes, llevo a lowercase y saco tildes
            aux = ' '+remove_non_unicode(aux.strip().lower())+' '

            #quito Numeros y Caracteres
            aux = remove_non_alphanumeric(aux)

            #quito espacios
            aux = remove_spaces(aux)

            document.steamed_content = aux
            document.save()

def load_words(request, ldamodel = None):
    cursor = connection.cursor()
    """Carga el diccionario a partir de las palabras previamente limpiadas"""


    print "Reading words we already have..."
    historic_words = []
    for w in Word.objects.all():
        historic_words.append(w.name)

    print "We have %s words..." % len(historic_words)

    dictionary = {}

    print "Loading words..."
    documents = Document.objects.filter(loaded_words = 0)

    i = 0
    print " -> %s documents loaded..." % len(documents)
    for d in documents:
        for a in d.cleaned_content.split(" "): dictionary[a] = 1

    goal = 0
    current = 0
    leng = len(dictionary)

    for d in dictionary:
        goal, current = avance(current, leng, goal)
        if d not in historic_words:
            w = Word(name = d)
            try:
                w.save()
            except Exception as e:
                #print e[0]
                if not int(e[0]) == 1062:
                    print "Fallo "+w.name
    print "  Words Loaded!"
    
    print "  Updating documents..."
    cursor.execute("UPDATE application_document SET loaded_words = 1 WHERE loaded_words = 0;")
    cursor.execute("COMMIT")
    print "  Documents Updated!"
    connection.close()


def get_freq(request, ldamodel = None):
    """calculos de la tabla frequency"""
    #LIMPIO LA TABLA
    cursor = connection.cursor()
    print "Getting Frequencies..."

    documents = Document.objects.filter(frec_calculated = 0)

    #Caluclo LAS FRECUENCIAS
    wf = {}
    words = {}
    for w in Word.objects.all():
        words[w.name] = w

    print "  Getting simple frequency calculated..."
    goal = 0
    current = 0
    leng = len(documents)
    i = 0
    for d in documents:
        goal, current = avance(current, leng, goal)

        wf.clear()
        #print "Counting Words..."
        if ldamodel and ldamodel.stemming and d.steamed_content:
            if i == 0: print "using stemming"
            i += 1
            content = d.steamed_content.split(' ')
        else:
            content = d.cleaned_content.split(' ')
        
        for s in content:
            wf[s] = wf.get(s,0) + 1

        #print "Saving..."
        freqs = []
        for kw in wf:
            try:
                freqs.append("("+str(d.id)+","+str(words[kw].id)+","+str(wf[kw])+")")
            except Exception as e:
                print "En documento %s error:" % d.id
                print e
        
        query = "INSERT INTO application_frequency (document_id, word_id, frequency) VALUES %s;" % ",".join(freqs)
        #print query

        cursor.execute(query)
        cursor.execute("COMMIT")
    print "  Simple frequency calculated!"
    
    print "  Getting max frequency..."
    cursor.execute("""UPDATE application_document D SET max_word_frec=(SELECT MAX(F.frequency) FROM application_frequency F WHERE F.document_id=D.id AND max_word_frec is NULL)""")
    print "  Max frequency calculated!"
    
    print "  Updating documents..."
    cursor.execute("UPDATE application_document SET frec_calculated = 1 WHERE frec_calculated = 0;")
    print "  Documents Updated!"

    cursor.execute("COMMIT")
    
    connection.close()

def get_worddatasetfreq():
    """ Calculo de frecuencia total de una palabra en un sitio """
    print """ Getting word-dataset frequency """
    cursor = connection.cursor()
    cursor.execute("""TRUNCATE application_worddatasetfrequency""")
    cursor.execute("""INSERT INTO application_worddatasetfrequency (word_id, dataset_id, frequency) (SELECT W.id, S.id, sum(F.frequency) FROM application_frequency as F, application_word as W, application_document as D, application_dataset as S where W.id=F.word_id and F.document_id=D.id and D.dataset_id=S.id GROUP BY W.name, S.id)""")
    cursor.execute("COMMIT")
    connection.close()

def get_wordldamodel(request, ldamodel):
    """Palabras que solo estan en ldamodel, su cantidad de apariciones y en cuantos documentos se encuentran"""

    print ""
    print "==================================================="
    print " > Calculating WordLDAmodel for "+ldamodel.name
    print "==================================================="

    select = """
    SELECT f.word_id,slm.ldamodel_id,COUNT(f.id), SUM(f.frequency) 
    FROM application_datasetldamodel slm 
    JOIN application_document d ON d.dataset_id = slm.dataset_id 
    JOIN application_frequency f ON f.document_id = d.id 
    WHERE slm.ldamodel_id = """+str(ldamodel.id)+""" AND d.test = 0
    GROUP BY f.word_id
"""

    cursor = connection.cursor()
    cursor.execute("INSERT INTO application_wordldamodel (word_id, ldamodel_id, n_doc_appearances, frequency) " + select)
    cursor.execute("COMMIT")
    connection.close()


def clean_low_freq(freq):
    """Limpieza de las palabras con bajas frecuencias en los modelos especificos"""

    print "Quito las palabras con baja frecuencia..."
    cursor = connection.cursor()
    cursor.execute("DELETE FROM application_wordldamodel WHERE frequency <= "+str(freq))
    cursor.execute("COMMIT")
    connection.close()

def set_distribution(ldamodel):
    """Transformacion para dejar los documentos como listas de los word id"""

    insert = """INSERT INTO application_documentdistribution (document_id, ldamodel_id, distribution) (
    SELECT 
        D.id, 
        SL.ldamodel_id, 
        group_concat(REPEAT(CONCAT(HEX(F.word_id),','),F.frequency) separator '') as distribution
    FROM application_frequency F
    JOIN application_wordldamodel W ON F.word_id = W.word_id AND W.ldamodel_id = """+str(ldamodel.id)+"""
    JOIN application_document D ON F.document_id = D.id
    JOIN application_dataset S ON S.id = D.dataset_id
    JOIN application_datasetldamodel SL ON S.id = SL.dataset_id
    WHERE SL.ldamodel_id = """+str(ldamodel.id)+"""
    GROUP BY D.id
    );"""

    print insert

    cursor = connection.cursor()
    cursor.execute("SET GLOBAL group_concat_max_len = 5000000;")
    cursor.execute("COMMIT")
    cursor.execute("DELETE FROM application_documentdistribution WHERE ldamodel_id = %s" % str(ldamodel.id))
    cursor.execute("COMMIT")
    cursor.execute(insert)
    cursor.execute("COMMIT")
    connection.close()

    print "  Distribuciones Asignadas..."

    return HttpResponse("Set distribution completed")

def remove_common_words(ldamodel):
    """ This method removes words which have similar frequency among diffrent datasets """
    print "Checking and Removing common words"

    remove_list = []

    n_of_datasets = DataSetLdaModel.objects.filter(ldamodel=ldamodel).count()
    datasets = DataSet.objects.filter(datasetldamodel__ldamodel = ldamodel)
    if n_of_datasets < 2: return

    lda_words = WordLdaModel.objects.filter(ldamodel=ldamodel)
    
    goal = 0
    current = 0
    leng = len(lda_words)

    for this_word in lda_words:

        goal, current = avance(current, leng, goal)
        freq_table = n_of_datasets*[0]
        #print freq_table
        wsf_involved = WordDataSetFrequency.objects.filter(word = this_word, dataset__in = datasets)
        #print wsf_involved

        for i in range(0,len(wsf_involved)):
            freq_table[i] = wsf_involved[i].frequency

        freq_tot = sum(freq_table)
        freq_avg = float(freq_tot)/n_of_datasets

        # Promedio deltas
        delta_avg = 0
        for i in range(0,n_of_datasets-1):
            for j in range(i+1,n_of_datasets):
                delta_avg += abs(freq_table[i]-freq_table[j])
        delta_avg = float(delta_avg)*2/((n_of_datasets-1)*n_of_datasets)

        # Remove
        if delta_avg < freq_avg:
            remove_list.append(str(this_word.id))

    if remove_list:
        
        sql = "DELETE FROM application_wordldamodel WHERE id IN (%s)" % ",".join(remove_list)
        cursor = connection.cursor()
        cursor.execute(sql)
        cursor.execute("COMMIT")
        connection.close()
        print " -> %s Words removed" % len(remove_list)

    else:
        print " -> No words removed"
