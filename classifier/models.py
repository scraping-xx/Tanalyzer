# -*- coding: UTF-8 -*-
#Native

#Django
from django.db import models
from django.db import connection

#Proyect
from application.models import LdaModel
from application.models import Topic
from application.models import Client
from application.models import Document

from classifier.views import predict

class Classifier(models.Model):
    """ Component used for classification """
    
    name = models.CharField(max_length = 255)
    #Starting model for the classifier
    ldamodel = models.ForeignKey(LdaModel)
    
    #Reviso si el cliente existe en la tabla de cliente, clasificador
    def validate(self,client):
        try:
            ClientClassifier.objects.get(client = client,classifier = self)
        except:
            return False
        return True
        
    #Obtiene las predicciones siguiendo los diferentes modelos en el arbol    
    def classify(self,ldamodel,content,cut,value):
        if not ldamodel or value < cut:
            return []
        else:
            return [{'topic':topic.id,'topic_label':topic.label,'value':value,'quality':quality,'keywords':keywords,'subtopics':self.classify(self.getModel(topic),content,cut,value)} for (topic,value,quality,keywords) in predict(ldamodel,content)]
    
    #Obtiene el modelo asociado al topic
    def getModel(self,topic):
        try:
            return ClassifierNode.objects.get(topic = topic,classifier = self).ldamodel
        except:
            #print topic.label,self.name
            return None
            
    #Retorna el modelo base para iniciar la clasificacion        
    def startModel(self):
        return self.ldamodel
    
    def __unicode__(self):
        return self.name
        
class ClassifierNode(models.Model):
    """ Node on the classification tree """
    
    classifier = models.ForeignKey(Classifier)
    #Topic of the father Node
    topic = models.ForeignKey(Topic)
    #Son model for next stage
    ldamodel = models.ForeignKey(LdaModel)

    def __unicode__(self):
        return self.classifier.name+" - "+self.topic.label+" : "+self.ldamodel.name

class ClientClassifier(models.Model):
    """ Which client is able to run which classifier """
    
    client = models.ForeignKey(Client)
    classifier = models.ForeignKey(Classifier)
    
    def __unicode__(self):
        return self.client.name+" - "+self.classifier.name


