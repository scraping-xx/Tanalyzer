from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

#Dajax
from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    #DajaxIce
    (r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),
    #Ajax
    (r'^ajax/prepare_data/$', 'application.ajax.prepare_data'),
    (r'^ajax/validation_data/$', 'application.ajax.validation_data'),
    (r'^ajax/train_data/$', 'application.ajax.train_data'),

    #Extraction
    (r'^extract/do/$', 'extract.views.do'),
    (r'^extract/do/(\d+)/(\d+)/$', 'extract.views.do'),
    (r'^extract/read_database/$', 'extract.views.read_database'),
    (r'^extract/set_test_partition/(\d+)/(\d+)/$', 'extract.views.set_test_partition'),


    #Transform: Define dictionary, clean text, etc
    (r'^transform/do/$', 'transform.views.do'),
    (r'^transform/do/(\d+)/$', 'transform.views.do'),

    #Tranining
    (r'^training/do/$', 'training.views.do'),
    (r'^training/do/(\d+)/$', 'training.views.do'),
    (r'^training/load_data/$', 'training.views.load_data_in_file'),

    #Data Manager
    (r'^datamanager/do/$', 'datamanager.views.do'),
    (r'^datamanager/do/(\d+)/$', 'datamanager.views.do'),
    (r'^datamanager/export_master_topic/(\d+)/$', 'datamanager.views.export_master_topics'),
    (r'^datamanager/import_master_topics/(\d+)/$', 'datamanager.views.import_master_topics'),

    #Application
    (r'^$', 'application.views.index'),
    (r'^application/$', 'application.views.index'),
    (r'^application/predict_data_set/(\d+)/(\d+)/(\d+)$', 'application.views.predict_data_set'),
    (r'^application/predict_ldamodel/(\d+)/(\d+)/(\d+)$', 'application.views.predict_ldamodel'),
    (r'^application/import/$', 'application.views.data_import'),
    (r'^application/show_model/(\d+)/$', 'application.views.show_model'),
    (r'^application/show_post/(\d+)/(\d+)/$', 'application.views.show_post'),
    (r'^application/classifier/$', 'application.views.classifier'),
    (r'^application/import/$', 'application.views.data_import'),
    (r'^application/validate/(\d+)/$', 'application.views.validation_sample'),
    (r'^application/validate/$', 'application.views.validation_sample'),
    (r'^application/create/(\d+)/$', 'application.views.create_documents_in_datasets'),

    #Classifier
    
    #Validator
    (r'^validation/do/(\d+)/(\d+)/$', 'validation.views.do'),
    (r'^validation/test/(\d+)/$', 'validation.views.test'),

    #Betazeta Webservice
    (r'^ws/betazeta/$', 'webservice.views.betazeta'),
    (r'^ws/test/$', 'webservice.views.test'),

    #Backend
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'admin/'),

    #Otros
    (r'^transform/remove_common_words/$', 'transform.views.remove_common_words'),
    (r'^transform/clean/$', 'transform.views.clean_content'),

    #(r'^test/$', 'transform.views.freeling_stemming'),
    #(r'^test2/$', 'initialize.views.install_freeling_api'),

    #Fast Classify
    (r'^application/fast/(\d+)/$', 'application.views.fast_classify'),
    (r'^application/newldamodel/(\d+)/$', 'application.views.newldamodel'),

    #Utilities for Thesis
    (r'^application/stopwords/$', 'application.views.stopwords_to_latex'),
    (r'^application/model/(\d+)/$', 'application.views.model_to_latex'),
    (r'^application/topic/(\d+)/$', 'application.views.topic_to_latex'),

)

