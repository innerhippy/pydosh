import operator
import csv
from PyQt4 import QtCore

class DecoderException(Exception):
	""" General Decoder exceptions
	"""
class Decoder(QtCore.QObject):
	def __init__(self, dateField, descriptionField, 
				creditField, debitField, currencySign, dateFormat, files, parent=None):
		super(Decoder, self).__init__(parent=parent)
		self.__dateField = None if dateField.isNull() else dateField.toInt()[0]
		self.__descriptionField = None if descriptionField.isNull() else descriptionField.toInt()[0]
		self.__creditField = None if creditField.isNull() else creditField.toInt()[0]
		self.__debitField = None if debitField.isNull() else debitField.toInt()[0]
		self.__currencySign = None if currencySign.isNull() else currencySign.toInt()[0]
		self.__dateFormat = None if dateFormat.isNull() else dateFormat.toString()
		self.__files = files
		self.__records = []

		for f in files:
			self.process(f)

	@property
	def records(self):
		return self.__records

	def process(self, filename):

		csvfile = QtCore.QFile(filename)

		if not csvfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
			raise DecoderException('Cannot open file %r' % filename)

		lineno = 0
		while not csvfile.atEnd():
			rawdata = dateField = descField = txDate = debitField = creditField = error = None

			try:
				rawdata = csvfile.readLine().trimmed()
				row = csv.reader([str(rawdata)]).next()
				dateField  = self.__getDateField(row[self.__dateField])
				descField  = self.__getDescriptionField(row[self.__descriptionField])
				txDate     = self.__getTransactionDate(row[self.__descriptionField], dateField)
				debitField = self.__getAmountField(row[self.__debitField], operator.lt)
				creditField = self.__getAmountField(row[self.__creditField], operator.gt)

				if debitField is None and creditField is None:
					raise DecoderException('No credit or debit found')

			except Exception, exc:
				error = '%s[%d]: %r' % (QtCore.QFileInfo(csvfile).fileName(), lineno, str(exc))

			finally:
				lineno += 1
				if len(rawdata):
					self.__records.append((rawdata, dateField, descField, txDate, debitField, creditField, error,))


	def __getDateField(self, field):
		date = QtCore.QDate.fromString(field, self.__dateFormat)

		if not date.isValid():
			raise DecoderException('Invalid date: %r' % field)

		return date

	def __getDescriptionField(self, field):
		return field.replace("'",'')

	def __getTransactionDate(self, field, dateField):

		#Format is "23DEC09 1210"
		rx = QtCore.QRegExp('(\\d\\d[A-Z]{3}\\d\\d \\d{4})')
		if rx.indexIn(field) != -1:
			return QtCore.QDateTime.fromString (rx.cap(1), "ddMMMyy hhmm").addYears(100)

		# Format is "06NOV10"
		rx = QtCore.QRegExp('(\\d{2}[A-Z]{3}\\d{2})')
		if rx.indexIn(field) != -1:
			return QtCore.QDateTime.fromString (rx.cap(1), "ddMMMyy").addYears(100)

		# Format is " 06NOV" <- note the stupid leading blank space..
		rx = QtCore.QRegExp(' (\\d\\d[A-Z]{3})')
		if rx.indexIn(field) != -1:
			# Add the year from date field to the transaction date
			return QtCore.QDateTime.fromString (rx.cap(1) + dateField.toString("yyyy"), "ddMMMyyyy")

		return None


	def __getAmountField(self, field, comp):
		value, ok = QtCore.QString(field).toDouble()
		if not ok:
			return

		value *= self.__currencySign

		if comp(value, 0.0):
			return value

		return None
