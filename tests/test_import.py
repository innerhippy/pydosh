# -*- coding: utf-8 -*-
""" Unit tests for import module
"""
import os
import unittest
import hashlib
from datetime import datetime

from pydosh.models import importModel


class TestCsvParse(unittest.TestCase):
	def setUp(self):
		raw = u'07/08/2016,Some Company,£2.40'
		self.rec = importModel.CsvRecordItem(raw)
		self.rec.formatItem(0, 1, 2, 2, -1, 'dd/MM/yyyy')
		self.data = self.rec.dataDict()
		
	def test_maxColums(self):
		self.assertEqual(self.rec.maxColumns(), 6)

	def test_isValid(self):
		self.assertTrue(self.rec.isValid())

	def test_numBadRecords(self):
		self.assertEqual(self.rec.numBadRecords(), 0)

	def test_data_raw(self):
		self.assertEqual(self.data['raw'], u'07/08/2016,Some Company,\xa32.40')

	def test_data_checksum(self):
		checksum = hashlib.md5(self.data['raw'].encode('UTF-8')).hexdigest()
		self.assertEqual(self.data['checksum'], checksum)

	def test_data_credit(self):
		self.assertEqual(self.data['credit'], None)

	def test_data_debit(self):
		self.assertEqual(self.data['debit'], -2.4)

	def test_data_date(self):
		self.assertEqual(self.data['date'], datetime(2016, 8, 7))

	def test_data_desc(self):
		self.assertEqual(self.data['desc'], u'Some Company')

	def test_currencies(self):
		cases = [
			(u'2.40', 2.4),
			(u'2', 2.0),
			(u'-2.40', -2.4),
			(u'-2', -2.0),
			(u'"2,000.40"', 2000.4),
			(u'"-2,000.40"', -2000.4),
			(u'£2.40', 2.4),
			(u'-£2.40', -2.4),
			(u'0.00', 0.0),
			(u'0', 0.0),
		]
		for amount, expected in cases:
			rec = importModel.CsvRecordItem(u'07/08/2016,Some Company,%s' % amount)
			sign = 1 if expected < 1 else -1
			rec.formatItem(0, 1, 2, 2, sign, 'dd/MM/yyyy')
			self.assertEqual(rec.dataDict().get('debit'), expected * sign)


	def test_debit_noSign(self):
		rec = importModel.CsvRecordItem(u'07/08/2016,Some Company,2.40')
		rec.formatItem(0, 1, 2, 2, -1, 'dd/MM/yyyy')
		self.assertEqual(rec.dataDict().get('debit'), -2.4)
		self.assertEqual(rec.dataDict().get('credit'), None)

	def test_debit_withSign(self):
		rec = importModel.CsvRecordItem(u'07/08/2016,Some Company,-2.40')
		rec.formatItem(0, 1, 2, 2, 1, 'dd/MM/yyyy')
		self.assertEqual(rec.dataDict().get('debit'), -2.4)
		self.assertEqual(rec.dataDict().get('credit'), None)

	def test_debit_noSign_pound(self):
		rec = importModel.CsvRecordItem(u'07/08/2016,Some Company,£2.40')
		rec.formatItem(0, 1, 2, 2, -1, 'dd/MM/yyyy')
		self.assertEqual(rec.dataDict().get('debit'), -2.4)
		self.assertEqual(rec.dataDict().get('credit'), None)

	def notest_debit_withSign_pound(self):
		rec = importModel.CsvRecordItem(u'07/08/2016,Some Company,-£2.40')
		rec.formatItem(0, 1, 2, 2, 1, 'dd/MM/yyyy')
		self.assertEqual(rec.dataDict().get('debit'), -2.4)
		self.assertEqual(rec.dataDict().get('credit'), None)




