# -*- coding: utf-8 -*-
#!/usr/bin/python

# Create your views here.
#Nativas
import urllib2
import re
import threading
import time
import os

#External
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import Comment

#Django
from django.db.models import Count
from django.http import HttpResponse
from django.conf import settings
from django.template import RequestContext

#Proyect
from application.models import * #Change
from django.conf import settings

#Proyect Libs
from lib.parser.soupselect import select
from lib.parser.functions import strip_tags
from lib.parser.functions import bzencode

def do(request,npost = 50,ldamodel_id = 1):
    
    #Leo desde Betazeta los documentos
    read(request,int(npost),int(ldamodel_id))

    #Setting test partition
    set_test_partition(request,0.1, int(ldamodel_id))

    return HttpResponse("Ok")

def read(request,npost = None, ldamodel_id = None):

    print "call"

    if not npost : npost = int(request.POST['npost'])
    if not ldamodel_id : ldamodel_id = int(request.POST['model'])

    print npost
    print ldamodel_id

    datasetldamodel = DataSetLdaModel.objects.filter(ldamodel__exact=ldamodel_id)
    count = len(datasetldamodel)

    print count

    dataset_total = 0
    for sm in datasetldamodel:
        dataset = sm.dataset
        npost += dataset_total
        last_document_finded = True
        print dataset.name
        print "=================="
            
        dataset_total = Document.objects.filter(dataset__exact=dataset.id).count()
        if dataset_total > 0:
            print "Ya existen posts..."
            last_document = Document.objects.filter(dataset__exact=dataset.id).order_by("-id")[0]
            last_document_finded = False
            print "Ultimo documento:"
            print last_document.url
        else:
            last_document = None
        npost -= dataset_total
        page_number = 1
        if not last_document_finded and dataset.post_per_page > 0: 
            page_number = dataset_total/dataset.post_per_page
            print "Starting fetch at page %s" % page_number

        documents = []
        document_number = 0
        while 1:
            #Abro pagina X de sitio web y leo aquellos divs que contienen links a articulos completos
            fullurl = dataset.url+"/page/"+str(page_number)
            print "Getting page..."
            print fullurl+"\n"
            try:
                soup  = BeautifulSoup(urllib2.urlopen(fullurl).read(),convertEntities=BeautifulSoup.HTML_ENTITIES,fromEncoding="utf-8")
            except Exception as e:
                print 'link corrupto' + fullurl
            divs = soup.findAll("article")
            
            article_count = 0
            hilos = {}
            
            for div in divs:
                #Leo el link y lo guardo
                urls = div.find("h2")
                urls = urls.find("a")
                documents += [urls["href"]] 
                article_url = urls["href"]

                if last_document_finded:
                    hilos[article_count] = threading.Thread(target = read_page, args=(dataset,article_url,document_number+article_count,))
                    hilos[article_count].start()
                    time.sleep(0.11)
                    article_count += 1
                else:
                    #print article_url
                    if last_document.url == article_url:
                        last_document_finded = True
                        print "Encontre Articulo!"

            for k in range(0,article_count):
                hilos[k].join()
                document_number += 1 
                if document_number >= npost :break
                            
            if document_number >= npost :break
            page_number += 1

        print "Obtenidos: #%s" % str(len(documents))
 
        sm.enabled = 0
        sm.save()

def read_page(dataset,article_url,n):

    try:
        htmlcode = unicode(urllib2.urlopen(article_url).read(),'utf-8')
    except Exception as e:
        print "Cant open url %s" %article_url
        print e
        print "Trying Again... "

        try:
            htmlcode = urllib2.urlopen(article_url).read()
        except Exception as ex:
            print "Cant open url %s" %article_url
            print e
            return None

    #Agregar Try Catch y clase de Log
    try:
        #Abro el articulo y voy al div con el contenido
        article_soup = BeautifulSoup(htmlcode,convertEntities=BeautifulSoup.HTML_ENTITIES,fromEncoding="utf-8")
        article_div = article_soup.find("div", attrs = eval(dataset.content_pattern))
        titulo = article_div.find("h1")
        titulo = titulo.contents[0]
    except Exception as e:
        print "Opening soup:"    
        print e
        print ""
        return None

    try:        
        #Fix muy flaite por un error de BF ya que los section los pone pegados no se pq.
        regex = re.compile('<section class="bodytext">((\t|\n|.)*?)</section>')
        section = regex.search(htmlcode, re.IGNORECASE).group(1)

        article_div = BeautifulSoup(section,convertEntities=BeautifulSoup.HTML_ENTITIES,fromEncoding="utf-8")

        #Obtengo los parrafos, los limpio y los almaceno en un string
        if article_div == None:
            ps = []
        else:
            ps = article_div.findAll("p")

    except Exception as e:
        print "Getting Soup"    
        print e
        print ""
        return None

    try:
        contents = []
        for p in ps:
            contents.append(str(strip_tags(str(p).replace('Link:','').replace('Links:',''))))                    
        contenido_articulo = " ".join(contents)
        contenido_articulo = re.sub("\n", "",contenido_articulo)
        contenido_articulo = contenido_articulo.strip()
    
    except Exception as e:
        print "Editing Soup"    
        print e
        print ""
        return None
            
    try:

        if contenido_articulo is not "":
            p = Document(
                title = titulo,
                original_content = contenido_articulo,
                url = article_url, dataset = dataset, 
                comments = 0, test = False,loaded_words = 0, frec_calculated = 0)

            p.save()
            print n,p.title

            return p
        else:
            return None

    except Exception as e:
        print "Saving Soup"    
        print e
        print ""
        return None


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


