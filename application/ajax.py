import json, pprint, traceback, sys

from dajax.core import Dajax
from dajaxice.decorators import dajaxice_register
from application.models import Topic
from django.http import HttpResponse

from training.views import do as training_do
from transform.views import do as transform_do
from datamanager.views import do as datamanager_do
from extract.views import set_test_partition

from lib.util.functions import timeit

@dajaxice_register
def save_label(request,new_label,id):

    topic = Topic.objects.get(pk = id)
    topic.label = new_label
    topic.save()

    return "ok"

@timeit
def prepare_data(request):
	
	model = int(request.GET['modelo'])
	if model == -1: model = None

	transform_do(request, model);

	return HttpResponse(json.dumps({'message':'Data prepared!','error':False}))

@timeit
def validation_data(request):
	
	model = int(request.GET['modelo'])
	test_data_size = int(request.GET['test_size'])

	set_test_partition(request,test_data_size, model)

	return HttpResponse(json.dumps({'message':"Test partition assigned! "+str(test_data_size)+"% of data for validation",'error':False }))

@timeit
def train_data(request):

	model = (request.GET['modelo'])
	if model == -1: model = None
	alpha = (request.GET['alpha'])
	beta = (request.GET['beta'])
	ntopics = (request.GET['ntopics'])
	try:
		training_do(request,model,alpha,beta,ntopics)
		datamanager_do(request,model)
	except Exception as e:
		exc_type, exc_value, exc_traceback = sys.exc_info()
		traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
		traceback.print_exc(file=sys.stdout)
		return HttpResponse(json.dumps({'message':str(e),'error':True}))
	
	return HttpResponse(json.dumps({'message':"Data training finish successful",'error':False}))

