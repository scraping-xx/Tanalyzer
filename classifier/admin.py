from django.contrib import admin

from tanalizer.classifier.models import Classifier
from tanalizer.classifier.models import ClassifierNode
from tanalizer.classifier.models import ClientClassifier

admin.site.register(Classifier)
admin.site.register(ClassifierNode)
admin.site.register(ClientClassifier)

