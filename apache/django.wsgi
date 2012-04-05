import os
import sys

sys.path.append('/home/camilo')
sys.path.append('/home/camilo/tanalizer')

os.environ['DJANGO_SETTINGS_MODULE'] = 'tanalizer.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
