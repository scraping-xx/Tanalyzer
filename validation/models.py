from django.db import models
from application.models import LdaModel, Topic, Document
from classifier.models import *

# Create your models here.
class Sample(models.Model):

    #Starting model for the classifier
    ldamodel = models.ForeignKey(LdaModel)

    #Topic selected
    topic = models.ForeignKey(Topic)

    #Text selected
    document = models.ForeignKey(Document)

class Segment(models.Model):
    """Segmentos en rangos 0-9, 10-19"""
    
    ini = models.IntegerField()
    end = models.IntegerField()

    def __unicode__(self):
        return str(self.ini)+'-'+str(self.end)


class CountDocSegTop(models.Model):
    """Guarda el numero de documentos donde un usuario dice un topic, y el algoritmo lo clasifico en un segmento"""
    ldamodel = models.ForeignKey(LdaModel) 
    segment = models.ForeignKey(Segment)
    topic = models.ForeignKey(Topic)
    count = models.IntegerField()


class DocSegTop(models.Model):
    """Guarda la separacion de los distintos topics dependiendo del segmento"""
    ldamodel = models.ForeignKey(LdaModel)
    document = models.ForeignKey(Document)
    topic = models.ForeignKey(Topic)
    segment = models.ForeignKey(Segment)
    quality = models.FloatField(null = True)
    value = models.FloatField(null = True)

    def __unicode__(self):
        return self.topic_label


