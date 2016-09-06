# -*- coding: utf-8 -*-
""" Unit tests for pydosh.currency module
"""
import os
import locale
import unittest

from pydosh import currency

class Currency(unittest.TestCase):

	def setUp(self):
		self.lang = os.environ.get('LANG')
		os.environ['LANG'] = ''

	def tearDown(self):
		if self.lang:
		    os.environ['LANG'] = self.lang

	def test_formatCurrency(self):
		self.assertEqual(currency.formatCurrency(23), u'23.00')
		self.assertEqual(currency.formatCurrency(23.00), u'23.00')
		self.assertEqual(currency.formatCurrency(23000), u'23,000.00')
		self.assertEqual(currency.formatCurrency(23000.00), u'23,000.00')
		self.assertEqual(currency.formatCurrency(-23000.00), u'-23,000.00')
		self.assertRaises(ValueError, currency.formatCurrency, u'23')

	def test_currencyCodes(self):
		self.assertTrue('GBP' in currency.currencyCodes())
		self.assertTrue('USD' in currency.currencyCodes())
		self.assertTrue('EUR' in currency.currencyCodes())

	def test_defaultCurrencyCode(self):
		self.assertEqual(currency.defaultCurrencyCode(), '')

	def test_toCurrencyStr(self):
		self.assertEqual(currency.toCurrencyStr(23, 'USD'), u'$23.00')
		self.assertEqual(currency.toCurrencyStr(23.00, 'USD'), u'$23.00')
		self.assertEqual(currency.toCurrencyStr(23000, 'USD'), u'$23,000.00')
		self.assertEqual(currency.toCurrencyStr(23000000.00, 'USD'), u'$23,000,000.00')

		self.assertEqual(currency.toCurrencyStr(23, 'GBP'), u'£23.00')
		self.assertEqual(currency.toCurrencyStr(23.00, 'GBP'), u'£23.00')
		self.assertEqual(currency.toCurrencyStr(23000, 'GBP'), u'£23,000.00')
		self.assertEqual(currency.toCurrencyStr(23000000.00, 'GBP'), u'£23,000,000.00')

class Currency_GB(Currency):
	def setUp(self):
		self.lang = os.environ.get('LANG')
		os.environ['LANG'] = 'en_GB.utf-8'

	def tearDown(self):
		os.environ['LANG'] = self.lang

	def test_defaultCurrencyCode(self):
		self.assertEqual(currency.defaultCurrencyCode(), 'GBP')

