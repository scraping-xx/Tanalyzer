import django.test as test
from application.models import Document,Topic,LdaModel, DataSet,DataSetLdaModel, DocumentDistribution, Frequency, Word,WordLdaModel,WordDataSetFrequency
from validation.models import Segment, DocSegTop
from django.db import connection
from django.test.client import Client

class ValidationTest(test.TestCase):

	fixtures = ['test_data.json']

	def setUp(self):
		pass

	def test_transform_all(self):
		
		#There are documents on the table

		dslm = DataSetLdaModel.objects.get(pk = 1)
		print "Enabled? ",dslm.enabled

		total_documents = Document.objects.all().count()
		self.assertTrue(total_documents > 0)

		#Document starts with l_w = 0
		ini_loaded_documents = Document.objects.filter(loaded_words = True).count()
		self.assertEqual(ini_loaded_documents, 0)
		
		#Document starts with f_c = 0
		ini_freq_documents = Document.objects.filter(frec_calculated = True).count()
		self.assertEqual(ini_freq_documents, 0)

		#Response 200
		client = Client()
		response = client.post('/transform/do/')
		self.assertEqual(response.status_code, 200)

		#Every document was set to l_w = 1
		loaded_documents = Document.objects.filter(loaded_words = 1).count()
		self.assertEqual(loaded_documents, total_documents)
		
		#Every document was set to f_c = 1
		freq_documents = Document.objects.filter(frec_calculated = 1).count()
		self.assertEqual(freq_documents, total_documents)

		#There are distributions
		total_distributions = DocumentDistribution.objects.all().count() 
		self.assertTrue(total_distributions>0)

		#There are frequencies
		total_frequency = Frequency.objects.all().count()
		self.assertTrue(total_frequency>0)

		#There are wordldamodelfreq
		total_wdf = WordDataSetFrequency.objects.all().count()
		self.assertTrue(total_wdf>0)

		#There are wordldamodel
		total_wl = WordLdaModel.objects.all().count()
		self.assertTrue(total_wl>0)

		#Distribution matrix test
		test_doc = Document.objects.get(pk = 1)
		doc_dist = DocumentDistribution.objects.get(document = test_doc)

		hex_word_ids = doc_dist.distribution.split(',')

		hex_words = [Word.objects.get(pk = int(hex_word_id,16)).name for hex_word_id in hex_word_ids if hex_word_id]
		c_content_words = test_doc.cleaned_content.split(" ")
		common_words_hex_and_content = list(set(c_content_words) & set(hex_words))

		not_relevant_words = list(set(c_content_words) - set(common_words_hex_and_content))
		
		#Ugly stuff, sorry, check if every word in not_relevant_words are actually not in the wordldamodel list of words
		#If they are not in that list that means that their frequency is low so they are not relevant  
		not_relevant_number = 0
		not_relevant_words_objects = []
		for not_relevant_word in not_relevant_words:
			word = Word.objects.get(name=not_relevant_word)
			not_relevant_words_objects.append(word)
			try:
				wmodel = WordLdaModel.objects.get(word = word, ldamodel__id = 1)
			except:
				not_relevant_number += 1
		
		#Check if there is low freq word for a model
		low_freq_words = WordLdaModel.objects.filter(frequency__lte = 5,ldamodel__id=1).count()
		high_freq_words = WordLdaModel.objects.filter(frequency__gt = 5,ldamodel__id=1).count()
		
		#Lest check if the words which where considered not relevant have actually a low freq:
		counter = 0
		for not_relevant_words_object in not_relevant_words_objects:
			counter += 1
			frequencies = Frequency.objects.filter(word = not_relevant_words_object)
			total_freq = 0
			for frequency in frequencies:
				total_freq += frequency.frequency
			#print not_relevant_words_object, total_freq, len(not_relevant_words_objects), counter
			if total_freq > 5:
				print ""
				print "  -> [!] Check if word '%s' was removed by distribution" % not_relevant_words_object.name
			
		vaca = Word.objects.get(name='vaca')
		documento = Document.objects.get(pk = 158)
		frecuencia = Frequency.objects.filter(word = vaca)

		dslm2 = DataSetLdaModel.objects.get(pk = 1)
		print "Enabled? ",dslm2.enabled

		self.assertEqual(0, low_freq_words)
		self.assertTrue( high_freq_words > 0)
		self.assertEqual(not_relevant_number, len(not_relevant_words))
		self.assertTrue(len(hex_words) <= len(c_content_words))
		self.assertEqual(len(set(hex_words)),len(common_words_hex_and_content))

		response = client.post('/training/do/')
		self.assertEqual(response.status_code, 200)

		response = client.post('/training/do/1/',{'ldamodel_id':1})
		self.assertEqual(response.status_code, 200)

		dslm3 = DataSetLdaModel.objects.get(pk = 1)
		print "Enabled? ",dslm3.enabled

	def transform_model(self):
		client = Client()
		response = client.post('transform/do/')

		self.assertEqual(response.status_code, 200)

