from BeautifulSoup import BeautifulSoup, NavigableString
from django.utils.encoding import smart_str, smart_unicode
import re
from django.utils.html import strip_tags as django_strip_tags
def strip_tags(data):
    data = re.compile(r'<.*?>').sub('',data)
    data = re.compile(r'\[.*?\]').sub('',data)
    data = re.compile(r'<!--*?-->').sub('',data)
    #data = django_strip_tags(data)
    return re.sub("\n", "",data)

def bzencode(string):
    return smart_str(string)

