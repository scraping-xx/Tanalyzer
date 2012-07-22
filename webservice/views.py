# -*- coding: UTF-8 -*-
#Native
import json

#Django
from django.http import HttpResponse
from django.http import HttpResponseNotFound

#Proyect
from application.models import * #Change
from classifier.models import * #Change

def betazeta(request):

    print request.POST

    id_cliente = 1
    # En el lambda se define un parser especial para cada cliente, 
    # para procesar un output especial
    response = webservice(request,id_cliente,lambda x: str({"cat":x}))

    return response

    if response:
        return HttpResponse(response)
    else:
        return HttpResponseNotFound()

def test(request):

    id_cliente = 1
    
    text = u"""Argentina: Se presentó el primer simulador de 
           vuelo diseñado sobre plataforma Linux Montado sobre
           un avion IA-50 Guaraní reciclado, el proyecto corre 
           sobre Ubuntu y la plataforma de simulación basada 
           en OpenGL, Flight Gear."""
    
    response = webservice(request,id_cliente,lambda x:x,1,text)
    if response:
        return HttpResponse(response)
    else:
        return HttpResponseNotFound()
    
    
def webservice(request,id_cliente,f,id_clasificador=None,text=None):

    #Obtener Post
    if not id_clasificador:
        id_clasificador = request.POST.get("classifier")
    
    if not text:
        text = request.POST.get("text")    
        
    document = Document(original_content = text)
    document.clean_content()

    #Obtener Cliente y Clasificador
    cliente = Client.objects.get(pk = id_cliente)
    clasificador = Classifier.objects.get(pk = id_clasificador)
    
    #Validar que Cliente posea dicho Clasificador
    if clasificador.validate(cliente):
        ldamodel = clasificador.startModel()
        prediccion = clasificador.classify(ldamodel,document.cleaned_content,10,11)
        return f(prediccion)
        
    else:
        print "Not Classified, you have not access to this classifier"
        return False
    
