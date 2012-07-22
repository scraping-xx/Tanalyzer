# -*- coding: utf-8 -*-
#!/usr/bin/python

# Create your views here.
#Nativas
import urllib2
import re
import threading
import time
import os
import math

#External
from bs4 import BeautifulSoup
from bs4 import Comment

#Django
from django.db.models import Count
from django.http import HttpResponse
from django.conf import settings
from django.template import RequestContext
from django.utils.encoding import smart_unicode, smart_str

#Proyect
from application.models import * #Change
from django.conf import settings

#Proyect Libs
from lib.parser.soupselect import select
from lib.parser.functions import strip_tags
from lib.parser.functions import bzencode

document_number = 0
last_document_finded = True
last_document = None

def do(request,npost = 50,ldamodel_id = 1):
    
    #Leo desde Betazeta los documentos
    read(request,int(npost),int(ldamodel_id))

    #Setting test partition
    set_test_partition(request,0.1, int(ldamodel_id))

    return HttpResponse("Ok")

def read(request,npost = None, ldamodel_id = None):

    global last_document_finded
    global last_document

    if not npost : npost = int(request.POST['npost'])
    if not ldamodel_id : ldamodel_id = int(request.POST['model'])
    datasetldamodel = DataSetLdaModel.objects.filter(ldamodel__exact=ldamodel_id)

    print npost
    print ldamodel_id
    print len(datasetldamodel)

    dataset_total = 0
    for sm in datasetldamodel:
        dataset = sm.dataset
        npost += dataset_total
        last_document_finded = True
        print dataset.name

        datasets = Document.objects.filter(dataset__exact=dataset.id)
        dataset_total = datasets.count()
        if dataset_total > 0:
            last_document = datasets.order_by("-id")[0]
            last_document_finded = False
        else:
            last_document = None

        npost -= dataset_total
        page_number = 1
        if not last_document_finded and dataset.post_per_page > 0: 
            page_number = int(math.ceil(dataset_total/dataset.post_per_page))
            print "Looking for last article at page %s" % page_number

        global document_number
        document_number = 0
        while 1:
            soup,html = get_front_page(dataset.url,page_number)
            urls = [div.find("h2").find("a") for div in soup.findAll("article")]
            get_articles(urls, npost, dataset)
            if document_number >= npost :break
            page_number += 1

        print "Obtenidos: #%s" % str(document_number)
 
        sm.enabled = 0
        sm.save()

def get_articles(urls,npost,dataset):

    global document_number
    global last_document_finded
    global last_document

    article_count = 0
    hilos = {}
    for url in urls:
        article_url = url["href"]

        if last_document_finded:
            hilos[article_count] = threading.Thread(target = read_page, args=(dataset,article_url,document_number+article_count,))
            hilos[article_count].start()
            time.sleep(0.11)
            article_count += 1
        else:
            if last_document.url == article_url:
                last_document_finded = True
                print "Encontre Articulo!"

    for k in range(0,article_count):
        hilos[k].join()
        document_number += 1 
        if document_number >= npost :break


def paginated_url(url,page_number):
    return url+"/page/"+str(page_number)

def get_front_page(url,page_number):
    fullurl = paginated_url(url,page_number)
    print "Getting page...\n\t%s\n" % fullurl
    return get_url(fullurl)

def get_url(url):

    try:
        htmlcode = get_contents_from_url(url)
    except Exception as e:
        print "Cant open url %s \n %s" % (url,e)
        try:
            htmlcode = get_contents_from_url(url)
        except Exception as ex:
            print "Cant open url %s \n %s" % (url,e)
            return None
    content = BeautifulSoup(htmlcode,'lxml',from_encoding="utf-8")
    return (content,htmlcode)

def get_article_title(article,pattern):

    article_div = article.find("div", attrs = pattern)
    title = article_div.find("h1").contents[0]
    return unicode(title)

def get_article_content(htmlcode):

    regex = re.compile('<section class="bodytext">((\t|\n|.)*?)</section>')
    section = regex.search(htmlcode, re.IGNORECASE).group(1)
    article_div = BeautifulSoup(section,'lxml',from_encoding="utf-8")
    ps = []
    if article_div: ps = article_div.findAll("p")
    contents = []
    for p in ps:
        contents.append(str(strip_tags(str(p).replace('Link:','').replace('Links:',''))))
    content = " ".join(contents)
    content = re.sub("\n", "",content)
    content = content.strip()
    return content


def read_page(dataset,article_url,n):

    article,htmlcode = get_url(article_url)
    title = get_article_title(article,eval(dataset.content_pattern))
    content = get_article_content(htmlcode)

    if content is not "":
        p = Document(
            title = title,
            original_content = content,
            url = article_url,
            dataset = dataset,
            comments = 0,
            test = False,
            loaded_words = 0,
            frec_calculated = 0
        )

        try:
            p.save()
        except Exception as e:
            print ">>>Saving Soup Error on: \n\t%s \n %s", (article_url,e)
            return None

        print n,p.title
        return p

    else:
        return None

def get_contents_from_url(url):
    return urllib2.urlopen(url).read()

def set_test_partition(request,test_data_size, ldamodel_id):

    print "Setting test partition"
    datasetldamodel = DataSetLdaModel.objects.filter(ldamodel__exact=ldamodel_id)
    documents_setted = 0

    for dm in datasetldamodel:
        dataset = dm.dataset
        print dataset.name
        total_document = Document.objects.filter(dataset__exact = dataset.id).count()
        test_documents = int(round(total_document*( float(test_data_size)/100)))
        documents_setted += test_documents

        cursor = connection.cursor()
        cursor.execute("UPDATE application_document d SET d.test=0  WHERE d.dataset_id = "+str(dataset.id)+" AND d.test=1")
        cursor.execute("COMMIT")
        update = "UPDATE application_document d SET d.test=1  WHERE d.id IN (SELECT * FROM (SELECT d.id FROM application_document d  WHERE  d.dataset_id = "+str(dataset.id)+" ORDER BY RAND() LIMIT 0,"+str(test_documents)+") A);"
        cursor.execute(update)
        cursor.execute("COMMIT")

    return HttpResponse(json.dumps({'Message':"%s Documents where set as test data on %s Datasets" % (str(documents_setted),str(len(datasetldamodel)))}))

def read_database(request):

    db_host = request.POST['db_host']
    db_user = request.POST['db_user']
    db_pass = request.POST['db_pass']
    db_name = request.POST['db_name']
    db_table = request.POST['db_table']

    d_title = request.POST['title']
    d_url = request.POST['url']
    d_dataset = request.POST['dataset']
    d_content = request.POST['content']
    d_id = request.POST['id']
    d_where = request.POST['where']
    if not d_where:
        d_where = 1

    test = 0
    local_db = settings.DATABASES['default']['NAME']
    local_user = settings.DATABASES['default']['USER']
    local_pass = settings.DATABASES['default']['PASSWORD']

    print "Extracting developer post from db %s table %s" % (db_name, db_table)

    mysqldump = "mysqldump -h %s -u %s -p%s %s %s --where='%s' --opt --quote-names --skip-set-charset --default-character-set=latin1 > /tmp/%s.dump" % (db_host, db_user, db_pass, db_name, db_table,d_where, db_name +'_'+ db_table)
    print mysqldump
    os.system(mysqldump) 
    print "  Extracted Table"

    if local_pass:
        command = "mysql -u %s -p%s --default-character-set=utf8 %s< /tmp/%s.dump" % (local_user, local_pass, local_db, db_name +'_'+ db_table)
    else:
        command = "mysql -u %s --default-character-set=utf8 %s< /tmp/%s.dump" % (local_user, local_db, db_name +'_'+ db_table)
    
    print command
    os.system(command)
    print "  Loaded Table"

    cursor = connection.cursor()

    if not d_url:
        d_url = "''"
    
    query = "INSERT INTO application_document (title, original_content, url, external_id, test, dataset_id,cleaned_content,steamed_content, loaded_words, frec_calculated) (SELECT %s, %s, %s, %s, %s, %s,'','', 0, 0 FROM %s)" % (d_title, d_content, d_url, d_id, test, d_dataset, db_table)
    
    print query
    cursor.execute(query)
    cursor.execute("COMMIT")

    print "  Loaded documents"
    connection.close()


