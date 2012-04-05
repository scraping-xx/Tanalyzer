# -*- coding: utf-8 -*-
#!/usr/bin/python

from subprocess import Popen, PIPE, STDOUT
import sys

#Django
from django.db.models import Count
from django.http import HttpResponse
from django.conf import settings
from django.template import RequestContext
from django.utils.encoding import smart_str, smart_unicode

#Proyect
from application.models import * 

def do(text):
    """Recibe un texto to_stem y retorna el stemed"""
    return freeling_stemming(text)

def freeling_stemming(text):
    
    stemmed_text = ""
    p = Popen(['stemmer/bin/analyze', '-f','stemmer/share/FreeLing/config/es.cfg','--utf','--nodate'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    c = p.communicate(input=text)[0]
    stem = c.split('\n')
    for s in stem:
        w = s.split(" ")
        if len(w) >=2: stemmed_text+=w[1]+" "
    return stemmed_text
    
