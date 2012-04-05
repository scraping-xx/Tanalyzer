# -*- coding: UTF-8 -*-
#Django
from django.http import HttpResponse, HttpResponseRedirect

#Proyect
from application.models import *
from validation.models import *
from application.views import predict_ldamodel,fast_classify

def do(request,class_id,ldamodel_id):
    #fast_classify(request,ldamodel_id)
    #predict_ldamodel(request,class_id,ldamodel_id,1)
    prepare(request,ldamodel_id)
    count_document_segment_topic(request,ldamodel_id)
    test(request,ldamodel_id)

    return HttpResponse("Ok")

def prepare(request,ldamodel_id):
    """Genera datos para validar un clasificador"""

    cursor = connection.cursor()
    cursor.execute("DELETE FROM validation_docsegtop WHERE ldamodel_id = %s" % ldamodel_id)
    cursor.execute("COMMIT")

    try:
        ldamodel = LdaModel.objects.get(pk = ldamodel_id)
    except Exception as e:
        print "->Error:can't retrieve ldamodel"
        print e

    try:
        datasets = DataSet.objects.filter(datasetldamodel__ldamodel = ldamodel)
        #.filter(datasetldamodel__enabled = 1)
    except Exception as e:
        print "->Error:can't retrieve datasets"
        print e

    documents_to_validate = []
    try:
        for ds in datasets:
            documents_sampled = Document.objects.filter(sample__ldamodel = ldamodel).distinct()
            documents_to_validate += Document.objects.filter(dataset = ds).filter(test = 1).filter(pk__in = documents_sampled)
    except Exception as e:
        print "->Error:can't retrieve documents"
        print e

    try:
        segments = Segment.objects.all()
    except Exception as e:
        print "->Error:can't retrieve segments"
        print e

    print ldamodel
    print 'segment ' + str(len(segments))
    print 'datasets ' + str(len(datasets))
    print 'documents_to_validate ' + str(len(documents_to_validate))

    for dtv in documents_to_validate:
        if dtv.prediction != '':
            #print dtv.prediction
            prediction = json.loads(dtv.prediction)
            for topic_value in prediction:
                topic = Topic.objects.get(pk = topic_value['topic'])
                for seg in segments:
                    if seg.ini < topic_value['value'] and topic_value['value'] < seg.end:
                        #print topic_value['value']
                        v = DocSegTop(ldamodel = ldamodel, document = dtv, topic = topic, segment = seg, value = topic_value['value'], quality = topic_value['quality'])
                        v.save()

    cursor.close()
    return HttpResponse("Ok")


def count_document_segment_topic(request, ldamodel_id):

    cursor = connection.cursor()
    cursor.execute("DELETE FROM validation_countdocsegtop WHERE ldamodel_id = %s" % ldamodel_id)
    cursor.execute("COMMIT")

    sql = """
    INSERT INTO validation_countdocsegtop (ldamodel_id, segment_id, topic_id, count) (
        SELECT DO.ldamodel_id, DO.segment_id, DO.topic_id, count(distinct DO.document_id) 
        FROM validation_docsegtop DO 
        WHERE DO.ldamodel_id = %d 
        GROUP BY DO.segment_id, DO.topic_id
    );
""" % (int(ldamodel_id))

    cursor = connection.cursor()
    cursor.execute(sql)
    cursor.execute("COMMIT")
    cursor.close()

    return HttpResponse("Calculo realizado")

def test(request,ldamodel_id):

    ldamodel = LdaModel.objects.get(pk=ldamodel_id)
    cursor = connection.cursor()

    print "LdaModel" + "\t" + "Alpha" + "\t" + "Beta" + "\t" + "Ntopics"
    print ldamodel.name + "\t" + str(ldamodel.alpha) + "\t" + str(ldamodel.beta) + "\t" + str(ldamodel.n_topics) 
    quality = 0
    delta = 1
    while quality<5 :  
    
        sql = "SELECT count(distinct document_id) FROM validation_docsegtop WHERE quality > %s AND ldamodel_id = %s" % (quality,ldamodel_id)
        cursor.execute(sql)
        n_documents = cursor.fetchone()[0]

        sql = "SELECT distinct document_id FROM validation_docsegtop WHERE quality > %s AND ldamodel_id = %s" % (quality,ldamodel_id)
        cursor.execute(sql)
        r = cursor.fetchall()
        quality_set = ",".join([str(a[0]) for a in r])
        
        print "Quality" + "\t" + "Tolerance" + "\t" + "Precision" + "\t" + "Recall" + "\t" + "F-Measure"+ "\t" + "Ndocs"

        for tolerance in range(1,35):
            precision = get_average_precision_for_tolerance(ldamodel_id,tolerance, quality,quality_set)
            recall = get_average_recall_for_tolerance(ldamodel_id,tolerance, quality,quality_set)
            if precision and recall:
                fmeasure  = 2/float(float(1/precision)+float(1/recall))
            else:
                fmeasure = 0
            print str(quality) + "\t" + str(tolerance) + "\t" + str(precision) + "\t" + str(recall) + "\t" + str(fmeasure) + "\t" + str(n_documents)
        quality += float(delta)

    return HttpResponse("Ok")

def get_average_recall_for_tolerance(ldamodel_id, tolerance, quality, quality_set):
    
    if not quality_set: return None 

    sql = """
SELECT ldamodel_id, AVG(recall) FROM(    
    SELECT S2.ldamodel_id, S2.topic_id, ( IF(S1.total IS NULL, 0, S1.total)/S2.total) as recall  
    FROM (
        SELECT VS.ldamodel_id,VS.topic_id, COUNT(*) AS total 
        FROM `validation_sample` VS 
        JOIN validation_docsegtop VD ON  
            VD.ldamodel_id = VS.ldamodel_id AND 
            VS.topic_id = VD.topic_id AND 
            VS.document_id = VD.document_id 
        WHERE value > %s AND VD.document_id IN (%s)
        GROUP BY topic_id, ldamodel_id
    )  S1 
    RIGHT JOIN (
        SELECT VD.ldamodel_id,VD.topic_id, COUNT(*) AS total 
        FROM validation_sample VD 
        WHERE VD.document_id IN (%s)
        GROUP BY topic_id, ldamodel_id
    ) S2 ON 
        S1.ldamodel_id = S2.ldamodel_id and 
        S1.topic_id = S2.topic_id
    WHERE S2.ldamodel_id = %s

) A GROUP BY ldamodel_id
""" % (tolerance, quality_set,quality_set,ldamodel_id)

    cursor = connection.cursor()
    cursor.execute(sql)
    r = cursor.fetchone()
    cursor.close()

    if r:
        return r[1]
    else:
        return None

def get_average_precision_for_tolerance(ldamodel_id,tolerance,quality,quality_set):

    if not quality_set: return None 

    cursor = connection.cursor()
    sql = """
SELECT ldamodel_id, AVG(prec) FROM(    
    SELECT S2.ldamodel_id, S2.topic_id, ( IF(S1.total IS NULL, 0, S1.total)/S2.total) as prec  
    FROM (
        SELECT VS.ldamodel_id,VS.topic_id, COUNT(*) AS total 
        FROM `validation_sample` VS 
        JOIN validation_docsegtop VD ON  
            VD.ldamodel_id = VS.ldamodel_id AND 
            VS.topic_id = VD.topic_id AND 
            VS.document_id = VD.document_id 
        WHERE value > %s AND VD.document_id IN (%s)
        GROUP BY topic_id, ldamodel_id
    )  S1 
    RIGHT JOIN (
        SELECT VD.ldamodel_id,VD.topic_id, COUNT(*) AS total 
        FROM validation_docsegtop VD 
        WHERE value > %s AND VD.document_id IN (%s)
        GROUP BY topic_id, ldamodel_id
    ) S2 ON 
        S1.ldamodel_id = S2.ldamodel_id and 
        S1.topic_id = S2.topic_id
    WHERE S2.ldamodel_id = %s
) A GROUP BY ldamodel_id
""" % (tolerance,quality_set,tolerance,quality_set,ldamodel_id)

    #print sql

    cursor.execute(sql)
    r = cursor.fetchone()
    cursor.close()

    if r:
        return r[1]
    else:
        return None

## Not used! ##

def get_precision(ldamodel_id):
    sql = """
SELECT S1.ldamodel_id, S1.topic_id, S1.segment_id, (S1.total/S2.count) as precison 
FROM (
    SELECT VS.ldamodel_id,VS.topic_id,VD.segment_id, COUNT(VD.segment_id) AS total 
    FROM `validation_sample` VS 
    JOIN validation_docsegtop VD ON  
        VD.ldamodel_id = VS.ldamodel_id AND 
        VS.topic_id = VD.topic_id AND 
        VS.document_id = VD.document_id 
    GROUP BY segment_id, topic_id, ldamodel_id
)  S1 
JOIN validation_countdocsegtop S2 ON 
    S1.ldamodel_id = S2.ldamodel_id and 
    S1.topic_id = S2.topic_id and 
    S1.segment_id = S2.segment_id
WHERE S1.ldamodel_id = %s 
""" % (int(ldamodel_id))

    cursor = connection.cursor()
    cursor.execute(sql)
    r = cursor.fetchall()
    cursor.close()

    return r

def get_topic_precision_for_tolerance(ldamodel_id, tolerance):

    sql = """
SELECT S2.ldamodel_id, S2.topic_id, ( IF(S1.total IS NULL, 0, S1.total)/S2.total) as precison  
FROM (
    SELECT VS.ldamodel_id,VS.topic_id, COUNT(*) AS total 
    FROM `validation_sample` VS 
    JOIN validation_docsegtop VD ON  
        VD.ldamodel_id = VS.ldamodel_id AND 
        VS.topic_id = VD.topic_id AND 
        VS.document_id = VD.document_id 
    WHERE value > %s
    GROUP BY topic_id, ldamodel_id
)  S1 
RIGHT JOIN (
    SELECT VD.ldamodel_id,VD.topic_id, COUNT(*) AS total 
    FROM validation_docsegtop VD 
    WHERE value > %s
    GROUP BY topic_id, ldamodel_id
) S2 ON 
    S1.ldamodel_id = S2.ldamodel_id and 
    S1.topic_id = S2.topic_id
WHERE S1.ldamodel_id = %s
""" % (tolerance,tolerance,ldamodel_id)

    cursor = connection.cursor()
    cursor.execute(sql)
    r = cursor.fetchall()
    cursor.close()

    return r

def get_topic_recall_for_tolerance(ldamodel_id, tolerance):

    sql = """
SELECT S2.ldamodel_id, S2.topic_id, ( IF(S1.total IS NULL, 0, S1.total)/S2.total) as recall  
FROM (
    SELECT VS.ldamodel_id,VS.topic_id, COUNT(*) AS total 
    FROM `validation_sample` VS 
    JOIN validation_docsegtop VD ON  
        VD.ldamodel_id = VS.ldamodel_id AND 
        VS.topic_id = VD.topic_id AND 
        VS.document_id = VD.document_id 
    WHERE value > %s
    GROUP BY topic_id, ldamodel_id
)  S1 
RIGHT JOIN (
    SELECT VD.ldamodel_id,VD.topic_id, COUNT(*) AS total 
    FROM validation_sample VD 
    GROUP BY topic_id, ldamodel_id
) S2 ON 
    S1.ldamodel_id = S2.ldamodel_id and 
    S1.topic_id = S2.topic_id
WHERE S2.ldamodel_id = %s
""" % (tolerance,ldamodel_id)

    cursor = connection.cursor()
    cursor.execute(sql)
    r = cursor.fetchall()
    cursor.close()

    return r
