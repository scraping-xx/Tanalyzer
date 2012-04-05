# -*- coding: UTF-8 -*-
#Native
import math
import datetime as DT
import sys

#Django
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response,get_object_or_404
from django.template import RequestContext
from django.core.cache import get_cache, cache
cache = get_cache('classifier')

#Proyect
from application.models import *
from classifier.models import *

#Proyect Libs
from lib.util.functions import * #Change
from lib.util.vector import * #Change
import json


def predict(ldamodel,content = None):
    """ Given a model and content, returns a set of topics related to the content according to the model """

    cache_time = 36000

    words = content.split(" ")
    total_words = len(words)
    not_in_dic = 0
    irrelevant_words = 0
    n_words = len(words)

    freq = {}
    score_nbm = {}
    doc_words = []
    aux_dic_word = {}

    #Calculo las frecuencias de cada palabra
    for w in words:
        aux_dic_word[w] = aux_dic_word.get(w,0)+1

    for w in aux_dic_word:
        try:
            """
            if cache.get("superwordcache"):
                allwords = cache.get("superwordcache")
                word = allwords[w]
            else:
                print "Start Caching"
                allwords = {}
                allwordsdic = Word.objects.all()
                for dictword in allwordsdic:
                    allwords[dictword.name] = dictword
                cache.set("superwordcache", allwords, cache_time)
                word = allwords[w]
                print "End Caching for super speed"
            """
            if cache.get("wordobj_"+w):
                word = cache.get("wordobj_"+w)
                sys.stdout.write(".")
            else:
                word = Word.objects.get(name=w)
                cache.set("wordobj_"+w, word, cache_time)
            freq[word.id] = aux_dic_word[w]
            doc_words += [word]
        except Exception:
            not_in_dic += aux_dic_word[w]

    topics = Topic.objects.filter(active=1).filter(ldamodel = ldamodel)
    val_factorial = math.factorial(9) #Parametro de ajuste pues aparecen valores muy pequeños

    topic_id = {}
    keywords = []
    n_keywords = 5

    for topic in topics:
        
        topic_id[topic.id] = topic
        topic_keywords = [] 

        #Guarda el puntaje para la prediccion de tipo Naive Bayes Multinomial
        score_nbm[topic.id] = 0  
        val = 0 
        hot_topic_counter = 1
        not_relevant_words = 1

        for word in doc_words:
        
            str_cache = str(ldamodel.id)+'.'+str(topic.id)+'.'+str(word.id)
            str_cache_fq = str_cache+"."+str(freq[word.id])
            
            if cache.get(str_cache_fq) is not None and cache.get(str_cache+"_val") is not None:
            
                #val tiene el valor NBM normalizado
                val = cache.get(str_cache_fq)
                #tw_val tiene el valor NBM original
                tw_val = cache.get(str_cache+"_val")
                topic_keywords.append((tw_val,word))
                #print "  -> [o] word %s from FULL cache..." % word.name
                
                if val is 0 : 
                    not_relevant_words += 1
            
            elif cache.get(str_cache+"_val") is not None:
            
                tw_val = cache.get(str_cache+"_val")
                topic_keywords.append((tw_val,word))
                val = naiveBayesMultinomial(tw_val,freq[word.id],val_factorial)
                cache.set(str_cache_fq, val, cache_time)
                #print "  -> [o] word %s from PART cache..." % word.name

            else:
                try:
                    topicw = Topicword.objects.get(topic = topic, word = word)

                    #print str(topicw) + str(topicw.value)
                    
                    try:
                        val = naiveBayesMultinomial(topicw.value,freq[word.id],val_factorial)
                        cache.set(str_cache_fq, val, cache_time)
                        tw_val = topicw.value
                        topic_keywords.append((tw_val,word))
                        cache.set(str_cache+"_val", tw_val, cache_time)
                    except Exception as e:
                        #Case: Error calculating val
                        val = 0
                        cache.set(str_cache_fq, val, cache_time)
                        cache.set(str_cache+"_val", val, cache_time)
                        print e
                except:
                    #Case: Word not relevant for topic
                    val = 0
                    not_relevant_words += 1
                    cache.set(str_cache_fq, val, cache_time)
                    cache.set(str_cache+"_val", val, cache_time)

            if val is not 0:
                score_nbm[topic.id] += math.ceil(val)
                if isHotTopic(normTopicValue(tw_val,True)):
                    hot_topic_counter += 1

        #Pondero el puntaje obtenido solo con las palabras en base a:
        # - las palabras mas importantes
        # - la cantidad de palabras del texto que no estan relacionados al topic

        score_nbm[topic.id] = (score_nbm[topic.id]*hot_topic_counter)/not_relevant_words
        if (score_nbm[topic.id] < 0): score_nbm[topic.id] = 0
        keywords.append(get_n_bests(topic_keywords,10))


    #Topic Quality
    quality = [float(score_nbm[key]/total_words) for key in score_nbm]
    #Normalizo los valores para que cada uno se mueva entre 0-100 y su suma total sea 100
    valores = map(lambda x: round(x*100),percent(score_nbm.values()))
    #Tomo los ids y los mapeo a sus TopicObj correspondientes
    topics = map(lambda x:topic_id[x],score_nbm.keys())

    #Retorno una lista [(TopicObj,Valor,Quality),...]
    return zip(topics, valores, quality,keywords)


def cut(l,cut = 0.1):
    return [(z,x,y,w) for (z,x,y,w) in l if x>=cut]

def get_n_bests(touples,n):
    touples.sort(reverse = True)
    touples = touples[:n]
    return [b.name for a,b in touples]

    


