from django.contrib import admin

from Tanalyzer.classifier.models import Classifier
from Tanalyzer.classifier.models import ClassifierNode
from Tanalyzer.classifier.models import ClientClassifier

admin.site.register(Classifier)
admin.site.register(ClassifierNode)
admin.site.register(ClientClassifier)

