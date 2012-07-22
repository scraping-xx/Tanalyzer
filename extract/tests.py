#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.utils import unittest
from application.models import Document,DataSet
from extract.views import *
from bs4 import BeautifulSoup

class ScrapperTestCase(unittest.TestCase):

    def setUp(self):
        #self.url = "http://www.fayerwayer.com/2012/07/instagram-podria-llegar-pronto-en-una-version-para-navegadores/"
        self.url = "http://www.ferplei.com/2012/07/ibrahimovic-poso-por-primera-vez-como-crack-del-psg-estoy-en-el-dream-team/"
        self.dataset = DataSet(name='test',url='http://www.test.com',content_pattern = '{"id":"main"}')
        self.dataset.save()
        self.document = Document(
            title = "test_article",
            url = self.url,
            dataset = self.dataset,
            comments = 0,
            test = False,
            loaded_words = 0,
            frec_calculated = 0
        )

    def save_article(self,content,id):
        self.document.original_content = content
        self.document.save()
        self.assertEqual(self.document.id,id)
        return self.document

    def test_bs_can_be_saved(self):
        contents = get_contents_from_url(self.url)
        soup = BeautifulSoup(contents,'lxml',from_encoding="utf-8")
        self.save_article(str(soup),1)

    def test_can_extract_and_save_webpage(self):
        contents = get_contents_from_url(self.url)
        self.save_article(contents,2)
        self.assertEqual(contents,self.document.original_content)

    def test_get_article(self):
        article,htmlcode = get_url(self.url)
        title = get_article_title(article, eval(self.dataset.content_pattern))
        self.assertTrue(article)
        self.assertTrue(htmlcode)
        #self.assertEqual(title,u'Instagram podría estrenar pronto una versión para navegadores')
        self.assertEqual(title,u'Ibrahimovic posó por primera vez como crack del PSG: “Estoy en el Dream Team”')
        self.save_article(title,3)

    def test_get_article_content(self):
        article,htmlcode = get_url(self.url)
        contents = get_article_content(htmlcode)
        self.save_article(contents,4)

    def test_paginated_url(self):
        self.assertEqual(paginated_url("test",4),"test/page/4")

    def test_read_page(self):
        article = read_page(self.dataset,self.url,1)
        self.assertEqual(article.id,5)
