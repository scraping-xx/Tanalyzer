# -*- coding: UTF-8 -*-

#Native
import math
import random
#Django
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext

#Proyect
from application.models import *
from classifier.models import *
from validation.models import *
from extract.views import read_database
from extract.views import read as scrap
from classifier.views import predict
from classifier.views import cut
from webservice.views import betazeta
from webservice.views import webservice
from training.views import do as training_do
from datamanager.views import do as datamanager_do

#Proyect Libs
from lib.util.functions import *
from django.contrib.auth.decorators import login_required

@login_required( login_url = '/admin/' )
@timeit
def validation_sample( request, ldamodel_id = None ):

    if request.method == "POST":
        
        if request.POST['send'] == "Go":
            return HttpResponseRedirect('/application/validate/'+request.POST['ldamodel']+'/')
        else:
            selected_topics = request.POST.getlist('topic')
            selected_document = request.POST['document']
            selected_ldamodel = ldamodel_id

            doc = Document.objects.get(pk=selected_document)
            lmod = LdaModel.objects.get(pk=selected_ldamodel)

            exist = Document.objects.filter(sample__ldamodel = lmod).filter(sample__document = doc).count()
            if not exist:
                for selected_topic in selected_topics:
                    sample = Sample()
                    sample.topic = Topic.objects.get(pk=selected_topic)
                    sample.document = doc
                    sample.ldamodel = lmod
                    sample.save()

                print "Sample Saved, document %s" % selected_document

    if ldamodel_id:

        cursor = connection.cursor()
        sql = "SELECT id from application_document WHERE test = 1 and id not in (SELECT distinct document_id FROM validation_sample where ldamodel_id = "+str(ldamodel_id)+") and dataset_id in (SELECT distinct dataset_id from application_datasetldamodel WHERE ldamodel_id = "+str(ldamodel_id)+") LIMIT 0,1;"
        cursor.execute(sql)
        r = cursor.fetchall()
        if r:
            document_id = r[0][0]
            document = Document.objects.get(pk = document_id)
            prediction = eval(document.prediction)
        else:
            document = None
            prediction = None

        sql = "SELECT count(distinct document_id) FROM validation_sample where ldamodel_id = "+str(ldamodel_id)
        cursor.execute(sql)
        evaluated = cursor.fetchone()[0]

        sql = "SELECT count(distinct id) FROM application_document where test = 1 AND dataset_id IN (SELECT distinct dataset_id from application_datasetldamodel WHERE ldamodel_id = "+str(ldamodel_id)+")"
        cursor.execute(sql)
        total = cursor.fetchone()[0]

        ldamodel = LdaModel.objects.get(pk=ldamodel_id)
        topics = Topic.objects.filter(ldamodel = ldamodel)

        return render_to_response('application/validate_document.tpl',{'prediction':prediction,'total':total,'model':ldamodel,'topics':topics,'document':document,'evaluated':evaluated},
            context_instance = RequestContext(request))

    else:

        ldamodels = LdaModel.objects.all()

        return render_to_response('application/validate.tpl',{'ldamodels':ldamodels},
            context_instance = RequestContext(request))


#@login_required(login_url='/admin/')
def predict_data_set(request,class_id,dataset_id,only_test_data):

    only_test_data = int(only_test_data)
    clasificador = get_object_or_404(Classifier, pk = class_id)
    dataset = get_object_or_404(DataSet, pk = dataset_id)
    
    print "=========================================="
    print "  Predicting Dataset %s" % dataset.name
    print "=========================================="

    if only_test_data == 1:
        documents = Document.objects.filter(dataset = dataset).filter(test = 1)
    else:
        documents = Document.objects.filter(dataset = dataset)

    doclen = len(documents)
    goal = 0
    current = 0
    for document in documents:
        goal, current = avance(current, doclen, goal)
        if not document.cleaned_content:
            document.clean_content()

        text = document.cleaned_content        
        if text:
            prediccion = webservice(request,1,lambda x:json.dumps(x),clasificador.id,text=text)
            document.prediction = prediccion
            document.save()
            #print "  -> [o] Document classified: %d" % document.id
        else:
            print "  -> [!] Removed Empty Document %d" % document.id
            print "  -> [!] URL: %s" % document.url
            document.delete()

    return HttpResponse('predicted')

#@login_required(login_url='/admin/')
def predict_ldamodel(request,class_id,ldamodel_id,only_test_data):

    ldamodel = LdaModel.objects.get(pk = ldamodel_id)
    dataset = DataSetLdaModel.objects.filter(ldamodel = ldamodel)

    for ds in dataset:
        #if ds.dataset.id == 8:
        predict_data_set(request, class_id, ds.dataset.id, only_test_data)

    return HttpResponse('predicted')

@login_required(login_url='/admin/')
def data_import(request):

    datasets = DataSet.objects.all()
    models = LdaModel.objects.all()
    success = ""

    if request.method == 'POST':
        
        if request.POST['form'] == 'scrap':
            scrap(request)
            success = "Scrap Succeded!"
        
        else:
            read_database(request)
            success = "Database Readed!"

    return render_to_response('application/import_index.tpl',{'datasets':datasets,'models':models,'success':success},
        context_instance = RequestContext(request))

@timeit
@login_required(login_url='/admin/')
def classifier(request):
    """ Allows to predict some text """

    text = ""
    sjson = ""
    jsoneval = ""
    message = ""

    if request.method == "POST":

        if request.POST['process'] == "one_text":

            text = request.POST['text']
            try:
                sjson = betazeta(request)
                jsoneval = eval(sjson)
                if not json:
                    sjson = "Empty response"
            except Exception as e:
                sjson = "There was an error, maybe too few relevant words for analysis"
                print e

        elif request.POST['process'] == "one_dataset":

            class_id = int(request.POST['classifier'])
            dataset_id = int(request.POST['dataset'])
            only_test_data = bool(request.POST['only_test_data'])

            predict_data_set(request,class_id,dataset_id,only_test_data)

            message = "Predictions asigned successfully."

        else:
            class_id = int(request.POST['classifier'])
            ldamodel_id = int(request.POST['ldamodel'])
            only_test_data = bool(request.POST['only_test_data'])

            predict_ldamodel(request,class_id,ldamodel_id,only_test_data)
            message = "Predictions asigned successfully!"


    classifiers = Classifier.objects.all()
    datasets = DataSet.objects.all()
    ldamodels = LdaModel.objects.all()
    return render_to_response('application/classifier_index.tpl',
        {'classifiers':classifiers,'text':text,'json':sjson,'jsoneval':jsoneval, 'datasets':datasets,'ldamodels':ldamodels},
        context_instance = RequestContext(request))

def fast_classify(request,ldamodel_id):

    cursor = connection.cursor()
    cursor.execute("DELETE FROM validation_sample WHERE ldamodel_id = %s" % ldamodel_id)
    cursor.execute("COMMIT")
    cursor.close()

    topics = Topic.objects.filter(ldamodel__id = ldamodel_id)   
    for topic in topics:
        if topic.id == 96 or topic.id == 129 or topic.id == 316:
            dataset_related_id = 1
        else:
            dataset_related_id = topic.get_related_dataset()
        dataset_related = DataSet.objects.get(pk = dataset_related_id)
        documents = Document.objects.filter(test = 1).filter(dataset = dataset_related)

        print str(dataset_related) +" -- "+ str(topic)
        for document in documents:
            sample = Sample(ldamodel_id = ldamodel_id,topic = topic, document = document)   
            sample.save()

    return HttpResponse("ok")

@login_required(login_url='/admin/')
def index(request):
    """ Selects a Model """

    if request.method == "POST":
        
        ldamodel_id = int(request.POST['modelo'])
        action = int(request.POST['action'])
        
        if action == 4:
            #print "Show"
            if ldamodel_id > 0: 
                return HttpResponseRedirect('/application/show_model/'+str(ldamodel_id)+'/')
            else:
                return HttpResponseRedirect('/application/show_model/1/')

    ldamodels = LdaModel.objects.all()

    return render_to_response('application/model_index.tpl',{'models':ldamodels},context_instance = RequestContext(request))

#@ensure_csrf_cookie
@login_required(login_url='/admin/')
def show_model(request,model_id):
    """ Show a LdaModel """
    ldamodel = get_object_or_404(LdaModel, pk = model_id)
    topics = Topic.objects.filter(ldamodel = ldamodel)
    """
    total_topic_score = 0

    for topic in topics:
        total_topic_score += topic.score

    for topic in topics:
        topic.score = topic.score/total_topic_score * 100
    """

    return render_to_response('application/model.tpl',{'topics':topics,'model':ldamodel})

@login_required(login_url='/admin/')
def show_post(request,model_id,document_id):
    """ Show a text analysis using a LdaModel """

    ldamodel = get_object_or_404(LdaModel, pk = model_id)
    document = get_object_or_404(Document, pk = document_id)

    if not document.cleaned_content:
        document.clean_content()
    
    #Obtengo la prediccion en base al modelo y NBM

    if ldamodel and ldamodel.stemming and d.steamed_content:
        text = document.steamed_content
    else:
        text = document.cleaned_content

    prediction = predict(ldamodel,text)
    #Dejo como topics relevantes solo los mayores a un 10% de participacion
    relevant_topics = cut(prediction,18)
    #Preparo el output, una lista de nombres
    relevant_topics = map(lambda (a,b,c,d): a.label,relevant_topics)
    
    #Construyo un nuevo formato para la prediccion, adecuado para el template
    prediction = dict(map(lambda (a,b,c,d):(a.id,b),prediction))
    
    words = text.split(" ")
    topics = Topic.objects.filter(active__exact = 1, ldamodel = ldamodel)
    topicword = {}

    print "Largo del texto %s" % len(words)
    
    for topic in topics:
        not_in_topic = 0
        not_in_dic = 0

        document_topic_score = int(math.ceil(Documenttopic.objects.filter(document = document).filter(topic = topic)[0].value*100))

        topicword[topic.id] = {}
        topicword[topic.id]['lda_score'] = document_topic_score
        topicword[topic.id]['prediction_score'] = prediction[topic.id]
        topicword[topic.id]['palabras'] = {}
        topicword[topic.id]['name'] = topic.label
        
        for w in words:
            topicword[topic.id]['palabras'][w] = 0
            try:
                word = Word.objects.get(name__exact = w)
                try:
                    topicw = Topicword.objects.get(topic = topic, word = word)
                    topicword[topic.id]['palabras'][w] = normTopicValue(topicw.value,True)
                except Exception as e:
                    #print "Word %s not found in topic %s" % (w,topic.id)
                    not_in_topic += 1
            except Exception:
                #print "Word %s not found in dictionary" % w
                not_in_dic += 1
        #print topicword[topic.id]
        print "Total de palabras no encontradas ",not_in_topic
        print "% de palabras no encontradas en " + topic.label
        print not_in_topic*100/len(words)
    
    return render_to_response('application/post.tpl',
        {'topicword':topicword.iteritems(),'documento':document,'prediction':relevant_topics,'model':ldamodel})

@timeit
@login_required(login_url='/admin/')
def create_documents_in_datasets(request, ndocs):

    ndocs = int(ndocs)
    words = Word.objects.all()
    datasets = DataSet.objects.all()
    max_word = len(words)
    total = 0

    for dataset in datasets:

        for j in range(0, ndocs):

            text = ""
            #text_len = 200
            base = 200
            variable = random.randint(0,5)
            text_len = base + variable
            for i in range(0, text_len):
                text += (words[random.randint(0,max_word-1)].name)+" "

            title = words[random.randint(0,max_word-1)].name+" "+words[random.randint(0,max_word-1)].name+" "+words[random.randint(0,max_word-1)].name
            
            Document(title = title, original_content = text, dataset = dataset).save()
            total += 1

    print "Total documents created: %s" % total

    return HttpResponse("ok")

def newldamodel(request, id_bzg):

    ldamodel = LdaModel(name = "Betazeta Generic "+str(id_bzg), alpha = 0, beta = 0, n_topics = 0, stemming = False)
    ldamodel.save()

    print ldamodel

    datasets = DataSet.objects.all()

    for dataset in datasets:
        dl = DataSetLdaModel(ldamodel = ldamodel, dataset = dataset)
        dl.save()
        print dl

    classif = Classifier(name = ldamodel.name, ldamodel = ldamodel)
    classif.save()

    print classif

    client = Client.objects.get(pk=1)
    cc = ClientClassifier(client = client, classifier = classif)
    cc.save()

    print cc

    return HttpResponse("Ready")



def stopwords_to_latex(request):

    sws = Stopword.objects.all()


    sws = sorted([sw.name for sw in sws])
    first_table = 25
    first_table_done = 0
    blocksize = 45
    blocknumber = 0
    columns = 7
    start = 0
    resizebox = 15
    concat = []

    assert(first_table < blocksize);

    for sw in sws:
        if start > columns - 1:
            first_block_condition = (not first_table_done and float(blocknumber % first_table) == 0 and blocknumber > 0)
            if (blocknumber > 0 and float(blocknumber % blocksize) == 0) or first_block_condition:
                print "    \\hline"
                print "  \\end{tabular}"
                print "   }"
                print "\\end{center}"
                print "\\end{table}"
                print ""

            if (blocknumber == 0 or float(blocknumber % blocksize) == 0) or first_block_condition:
                print "\\begin{table}"
                print "\\begin{center}"
                print "  \\resizebox{"+str(resizebox)+"cm}{!}{"
                print "  \\begin{tabular}{|"+" | ".join(["c"]*columns)+"" +"|}"
                print "    \\hline"
                print "        \\multicolumn{"+str(columns)+"}{|c|}{Stop Words} \\\\"
                print "    \\hline"
            if first_block_condition:
                first_table_done = 1
                blocknumber = 0

            print "    "+" & ".join(concat)+' \\\\'
            start = 0
            concat = []
            blocknumber += 1
        
        concat.append(sw)
        start += 1

    print "    \\hline"
    print "  \\end{tabular}"
    print "  }"
    print "\\end{center}"
    print "\\end{table}"

    return HttpResponse("ok, copy from terminal or log");

         
def topic_to_latex(request, topic_id):

    topic = Topic.objects.get(pk = topic_id)

    n = 10

    keywords = topic.get_words(n)

    print "Words"
    print "====================="
    
    for keyword in keywords:
        print "    "+keyword.word.name+" & "+str(keyword.value)+" \\\\"

    print ""
    print "Documents"
    print "====================="
    docs = topic.get_documents(n)
    for doc in docs:
        print "    "+doc.document.title+" & "+str(doc.value)+" \\\\"

    touples = zip( keywords, docs )
    touples = [(touple[0].word.name,touple[1].document.title,touple[1].document.dataset.name) for touple in touples]

    print ""
    print "All"
    print "====================="
    for touple in touples:
        print "    "+touple[0]+" & "+touple[1]+" "+"\\emph{"+touple[2]+"}"+" \\\\"

    return HttpResponse("ok, copy from terminal or log");

def model_to_latex(request, model_id):

    model = LdaModel.objects.get(pk = model_id)
    topics = Topic.objects.filter(ldamodel = model)
    for topic in topics:

        keywords = topic.get_words(10)
        words = [keyword.word.name for keyword in keywords]
        print topic.label+" & "+" ".join(words)+" \\\\"

    return HttpResponse("ok, copy from terminal or log");

