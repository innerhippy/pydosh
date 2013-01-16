import pdb
import operator
import csv
from PyQt4 import QtCore
import enum

class DecoderException(Exception):
	""" General Decoder exceptions
	"""
class Decoder(QtCore.QObject):
	def __init__(self, files, parent=None):
		super(Decoder, self).__init__(parent=parent)
		self.__files = files
#	def __init__(self, dateField, typeField, descriptionField, 
#				creditField, debitField, currencySign, dateFormat, files, parent=None):
#		super(Decoder, self).__init__(parent=parent)
#		self.__dateField = None if dateField.isNull() else dateField.toInt()[0]
#		self.__descriptionField = None if descriptionField.isNull() else descriptionField.toInt()[0]
#		self.__creditField = None if creditField.isNull() else creditField.toInt()[0]
#		self.__debitField = None if debitField.isNull() else debitField.toInt()[0]
#		self.__currencySign = None if currencySign.isNull() else currencySign.toInt()[0]
#		self.__dateFormat = None if dateFormat.isNull() else dateFormat.toString()
#		self.__files = files

		self.__dateField = 0
		self.__descriptionField = 2
		self.__creditField = 3
		self.__debitField = 3
		self.__currencySign = 1
		self.__dateFormat = 'dd/MM/yyyy'
		self.__records = []

		for f in files:
			self.process(f)

	@property
	def records(self):
		return self.__records
		
	def process(self, filename):

		with open(filename, 'rb') as csvfile:
			for line in csvfile:
				row = csv.reader([line]).next()
				rawdata = line.strip()
				dateField = descField = txDate = debitField = creditField = error = None
				try:
					
					dateField  = self.__getDateField(row[self.__dateField])
					descField  = self.__getDescriptionField(row[self.__descriptionField])
					txDate     = self.__getTransactionDate(row[self.__descriptionField], dateField)
					debitField = self.__getAmountField(row[self.__debitField], operator.lt)
					creditField = self.__getAmountField(row[self.__creditField], operator.gt)
				except IndexError:
					continue

				except DecoderException, exc:
					self.setError(str(exc))
					error = str(exc)

				finally:
					self.__records.append((rawdata, dateField, descField, txDate, debitField, creditField, error, ))

		from models import ImportModel
		from database import db
		db.connect()
		model = ImportModel(self.__records, self)
		

	def __getDateField(self, field):
		date = QtCore.QDate.fromString(field, self.__dateFormat)

		if not date.isValid():
			raise DecoderException('Invalid date: %r' % field)

		return date

	def __getDescriptionField(self, field):
		return field.replace("'",'')

	def setError(self, error):
		print error
		
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
			raise DecoderException('Invalid debit field: %r' % field)
	
		value *= self.__currencySign

		if comp(value, 0.0):
			return value

		return None

	"""
void
CSVDecoder::import(const QString& filename)
{
	QFile file(filename);
	
	if (!file.open(QIODevice::ReadOnly)) {
		qWarning() << "Cannot open file "  << file.fileName();
		return;
	}
	
	QTextStream in(&file);
	
	while (!in.atEnd()) {
		CSVParser csv(in.readLine());

		// Skip blank lines
		if (!csv.size()) 
			continue;

		// If the line doesn't being with a valid date field, then skip it
		if (!QDate::fromString(csv.get(m_fieldMap[DateField]), m_dateFormat).isValid()) {
			continue;
		}
		
		m_errorMessage.clear();

		// Initialise the CSV record with the raw data
		ImportRecord record(csv.line());
		
		// decode csv fields
		record.date = getDateField(csv);

		record.type = getTypeField(csv);
		record.description = getDescriptionField(csv);
		record.txDate = extractTransactionDate(record);
		record.credit = getCreditField(csv);
		record.debit = getDebitField(csv);
		record.balance = getBalanceField(csv);

		if (record.credit == 0.0 && record.debit == 0.0) {
			setError("No credit or debit found");
		}

		record.valid = isValid();
		record.error = m_errorMessage;

		m_errorMessage.clear();
		m_records.append(record);
	}
}

void
CSVDecoder::setError(const QString& message)
{
	if (!m_errorMessage.isEmpty())
		m_errorMessage += ", ";

	m_errorMessage += message;
}






	"""