# -*- coding: utf-8 -*-
import unicodedata, re

def remove_non_unicode(s):
    return unicodedata.normalize('NFKD', unicode(s)).encode('ascii', 'ignore')

def remove_spaces(s):
    return re.sub('\s+',' ',s)

def remove_non_alphanumeric(s):
    l = u'a-záéíóúüñA-ZÁÉÍÓÚÜÑ'
    if not isinstance(s, unicode):
        s = unicode(s, 'utf-8')
    
    starts = [match.start() for match in re.finditer(re.compile(u'['+l+']\-[0-9]|[0-9]\-['+l+']'), s)]
    i = 0
    for n in starts:
        s = s[:n+1-i]+s[n+2-i:]
        i+=1
    
    s=re.compile(u'[^'+l+'0-9 ]+').sub(u' ',s)
    s=re.compile(u'\\b\\d+(e *\\d+)?\\b').sub(u' ',s) # numros y notacion exp.(ie '1e 25')
    return re.compile(u' +').sub(u' ',s)

def remove_words(s,words):
    pattern = re.compile(words)
    return pattern.sub(' ',pattern.sub(' ',pattern.sub(' ',s)))
