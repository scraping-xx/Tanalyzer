from django.contrib import admin

from Tanalyzer.application.models import *

admin.site.register(Client)
admin.site.register(DataSet)
admin.site.register(LdaModel)
admin.site.register(Topic)
admin.site.register(Word)
admin.site.register(WordLdaModel)
admin.site.register(Document)
admin.site.register(DocumentDistribution)
admin.site.register(Stopword)
admin.site.register(DataSetLdaModel)

