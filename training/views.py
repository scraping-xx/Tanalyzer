#!/usr/bin/env 
# -*- coding: UTF-8 -*-
#Native
import os

#External
from numpy import *
from deltaLDA import deltaLDA

#Django
from django.db import connection
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

#Proyect
from application.models import * #Change
from lib.util.functions import avance, getbest, timeit

@timeit
def do(request, ldamodel_id = None, palpha = None, pbeta = None, pntopics = None):

    #Default Params
    alpha = .1
    beta = 1
    ntopics = 15

    if palpha and palpha != "":
        alpha = float(palpha)

    if pbeta and pbeta != "":
        beta = float(pbeta)

    if pntopics and pntopics != "":
        ntopics = int(pntopics)

    if not ldamodel_id or int(ldamodel_id) == -1:
        ldamodels = LdaModel.objects.all()
        for ldamodel in ldamodels:
            ldamodel.alpha = alpha
            ldamodel.beta = beta
            ldamodel.n_topics = ntopics
            ldamodel.save()
    else:

        ldamodel = LdaModel.objects.get(pk = ldamodel_id)
        ldamodel.alpha = alpha
        ldamodel.beta = beta
        ldamodel.n_topics = ntopics
        ldamodel.save()
        try:
            status = cross_lda(ldamodel, ntopics, alpha,beta)
        except Exception as e:
            raise e
        if not status:
            return HttpResponse("Error al ejecutar LDA, problemas de configuracion")

    return HttpResponse("OK")

def load_data_in_file():
    
    cursor = connection.cursor()
    cursor.execute("LOAD DATA INFILE '/tmp/application_topicword.txt' INTO TABLE application_topicword FIELDS TERMINATED BY ';' LINES TERMINATED BY '\n' (topic_id, word_id, value); ")
    return HttpResponse("insertion completed")

def cross_lda(ldamodel, n_topics, alpha, beta):
    """ Set some configurations before running LDA """

    print "###################################"
    print "Training Model : "+ldamodel.name
    print "###################################"
    #Elimina las a asociaciones con el modelo, topics, topic_word, topic_document, wordldamodel
    ldamodel.removeReferences()
    
    topic_local_to_universal = {}
    for i in range(n_topics):
        t = Topic(label = "Model "+str(ldamodel.id)+":Topic "+str(i+1), ldamodel = ldamodel, active = 1)
        t.save()
        topic_local_to_universal[i] = t.id
        
    documents_dist = DocumentDistribution.objects.filter(ldamodel = ldamodel)
    return lda(documents_dist,topic_local_to_universal,alpha,beta)

def lda(documents_dist,topic_local_to_universal,alpha,beta):
    """ Runs LDA over a set of documents, saving results over a set of predefined topics """

    cursor = connection.cursor()
    n_topics = len(topic_local_to_universal)
    
    word_local_to_universal = {}
    word_universal_to_local = {}
    
    document_local_to_universal = {}
    
    print "Getting document matrix..."

    dic = [word_mapper(map(lambda x: int(str(x),16),document_dist.distribution[:-1].split(',')),word_local_to_universal,word_universal_to_local) for document_dist in documents_dist]
    document_local_to_universal = dict(enumerate([document_dist.document.id for document_dist in documents_dist]))

    n_documents = str(len(dic))
    n_words = len(word_local_to_universal)
    
    print "Numero de documentos: "+str(n_documents)
    print "Numero de palabras: "+str(n_words)
    
    if int(n_documents) == 0:
        raise Exception('LDAmodel has no documents assigned or the documents had only irrelevant words. No document matrix founded.')
    
    f_label = 1
    numsamp = 50
    randseed = 194582

    alpha_vector = alpha * ones((f_label,n_topics))
    beta_vector = beta * ones((n_topics,n_words)) 

    print "Calculating LDA using..."
    print "   beta: "+str(beta)
    print "   alpha: "+str(alpha)
    print "   ntopics: "+str(n_topics)

    (phi,theta,sample) = deltaLDA(dic,alpha_vector,beta_vector,numsamp,randseed)
    print "Saving Results..."
    
    ########################
    #    document_topic
    ########################
              
    print "Saving Document and topic correlation..."
    document_local_id = 0
    goal = 0
    current = 0
    theta_len = len(theta)
    for d in theta:
        st = "INSERT INTO application_documenttopic (document_id, topic_id, value) VALUES "
        goal, current = avance(current, theta_len, goal)
        topic_local_id = 0
        for document_weight in d:
            st = st + "("+str(document_local_to_universal[document_local_id])+","+str(topic_local_to_universal[topic_local_id])+","+str(document_weight)+"),"
            topic_local_id += 1
        st = st[:-1]+";"
        cursor.execute(st)
        cursor.execute("COMMIT")
        document_local_id += 1
    
    #####################          
    #    topic_word
    #####################
    
    print "Saving topics and word correlation to file"
    topic_local_id = 0
    goal = 0
    current = 0
    phi_len = len(phi)
    nbest = int(n_words*0.5)


    os.system("touch /tmp/application_topicword.txt")
    os.system("chmod 777 /tmp/application_topicword.txt")
    FILE = '/tmp/application_topicword.txt'
    print 'Opening %s' % FILE
    fw = open (FILE,'w')
    
    for t in phi:
        goal, current = avance(current, phi_len, goal)
        word_local_id = 0
        for word_weight in t:
            fw.write(str(topic_local_to_universal[topic_local_id])+';'+str(word_local_to_universal[word_local_id])+';'+str(word_weight)+'\n')
            word_local_id += 1
        topic_local_id += 1

    fw.close()
    
    load_data_in_file()
    
    return True
    
def word_mapper(document_distribution,word_local_to_universal,word_universal_to_local):
    """Asigns correlative ids to a given set of words, saving the master list"""   
    new_doc_matrix = []
    for word in document_distribution:
        if word not in word_universal_to_local:
            new_id = len(word_universal_to_local)
            word_universal_to_local[word] = new_id
            word_local_to_universal[new_id] = word
        new_doc_matrix.append(word_universal_to_local[word])
            
    return new_doc_matrix

