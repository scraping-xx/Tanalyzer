from application.models import *
from django.http import HttpResponse,HttpResponseRedirect
from time import gmtime, strftime
import json

MASTER_TOPIC_LENGTH = 100

def do(request,ldamodel_id = None):
    score_relevance(request,ldamodel_id)
    set_dataset_labels(request,ldamodel_id)
    import_master_topics(request,ldamodel_id)
    return HttpResponse("Ready!") 

def score_relevance(request,ldamodel_id = None):

    if not ldamodel_id:
        topics = Topic.objects.all()
    else:
        topics = Topic.objects.filter(ldamodel__id = ldamodel_id)

    for t in topics:
        t.score = t.get_points()
        t.dataset_relevance = t.get_dataset_relevance()
        t.save()
    return HttpResponse("Score topic and DataSet relevance calculated") 

########################

def set_dataset_labels(request,ldamodel_id = None):

    if not ldamodel_id:
        topics = Topic.objects.all()
    else:
        topics = Topic.objects.filter(ldamodel__id = ldamodel_id)    

    #topics = Topic.objects.all()
    scores = []
    for t in topics:
        scores.append(round(t.score))
    m = 0
    topics = Topic.objects.all()
    tol = 2
    i = 1
    for t in topics:
        if t.score > m + tol:
            aux = t.dataset_relevance.replace("'",'"').replace(' u"',' "')
            di = json.loads(aux)
            maxi = 0
            lab = '--'
            for d in di:
                if float(d['value']) > float(maxi):
                    
                    maxi = float(d['value'])
                    lab = d['name']

            t.label = lab
            t.active = 1
            t.save()
        else:
            t.label = 'Topic '+str(i)
            i += 1
            t.active = 0
            t.save()
    return HttpResponse("set labels") 

########################
def export_master_topics(request, topic_id):
    ret = {}

#extraer las palabras del topic
#extraer los master-topics
#si existe un master-topic parecido al topic
#no hacer nada, devolver que ya existe
#sino
#agregarlo

    topic_word_to_add = []
    try:
        topic = Topic.objects.get(id = topic_id)
        topic_word_to_add = [topic.label,[topicword.word_name() for topicword in topic.get_words(MASTER_TOPIC_LENGTH)]]
    except Exception as e:
        ret['status'] = 'false'
        ret['message'] = 'get topic id error'
        return HttpResponse(json.dumps(ret,True))

    master_topics = []
    try:
        fr = open('mastertopics.txt', 'r')
    except Exception as e:
        ret['status'] = 'false'
        ret['message'] = 'open file error'
        return HttpResponse(json.dumps(ret,True))    

    try:
        for line in fr:
            if line != '':
                master_topics.append(json.loads(line))
        fr.close()
    except Exception as e:
        ret['status'] = 'false'
        ret['message'] = 'cant load json lines'
        return HttpResponse(json.dumps(ret,True))

    exist = 0
    for mt in master_topics:
        if topic_distance(mt,topic_word_to_add) == 0:
            #if equal_topic(mt,topic_word_to_add):
            master_topics.remove(mt)
            master_topics.append(topic_word_to_add)
            exist = 1
            if topic_word_to_add[0] == mt[0]:
                ret['status'] = 'true'
                ret['message'] = 'master topic already exist'
            else:
                ret['status'] = 'true'
                ret['message'] = 'name updated'
            break

    if exist == 0:
        master_topics.append(topic_word_to_add)
        ret['status'] = 'true'
        ret['message'] = 'master topic aggregate'

    fr = open('mastertopics.txt', 'w')
    for mt in master_topics:
        fr.write(json.dumps(mt,True))
        fr.write('\n')
    fr.close()
    return HttpResponse(json.dumps(ret,True))


def import_master_topics(request,ldamodel_id):
    
    print "Setting Labels From MasterFile..."

    counter = 0
    master_topics = []
    for line in open('mastertopics.txt', 'r'): master_topics.extend([json.loads(line)])

    if not ldamodel_id:
        topics = Topic.objects.all()
    else:
        topics = Topic.objects.filter(ldamodel__id = ldamodel_id)

    #print len(topics)

    for topic in topics:
        words = [topicword.word_name() for topicword in topic.get_words(MASTER_TOPIC_LENGTH)]
        best_topic = (2,'label')
        for master_topic in master_topics:
            distance = topic_distance(master_topic[1],words)
            if distance < best_topic[0]:
                best_topic = (distance,master_topic[0])
        if best_topic[0] < 0.6:
            topic.label = best_topic[1]
            topic.save()
            counter += 1

    print "  Process Ended, "+str(counter)+" where asigned."

    if not ldamodel_id:
        return HttpResponseRedirect('/application/show_model/1/')
        #SE CAIA CUANDO NO HABIA LDAMODEL_ID
    else:
        return HttpResponseRedirect('/application/show_model/%d/' % int(ldamodel_id))


# 1 es completamente distinto, 0 son iguales
def topic_distance(a,b):
    diff_list = [item for item in a if not item in b]
    return float(len(diff_list)/float(len(a)))

