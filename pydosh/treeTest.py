from PyQt4 import QtGui, QtCore, QtSql
QtCore.pyqtRemoveInputHook()
import pdb
import sys
import re

from database import db
import csv
import enum
import utils
#from dialogs import unicode_csv_reader

class DecoderError(Exception):
	""" General Decoder exceptions
	"""

class ImportException(Exception):
	""" General exception for record import
	"""

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
	# csv.py doesn't do Unicode; encode temporarily as UTF-8:
	csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
						dialect=dialect, **kwargs)
	for row in csv_reader:
		# decode UTF-8 back to Unicode, cell by cell:
		yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
	for line in unicode_csv_data:
		yield line.encode('utf-8')

class TreeItem(object):
	def __init__(self):
		super(TreeItem, self).__init__()
		self._parent = None
		self._error = None
		self._children = []

	def isValid(self):
		return True

	def isImported(self):
		return False

	def numRecordsToImport(self):
		""" Returns the number of records left that can be imported
		"""
		num = 1 if self.canImport() else 0
		for child in self._children:
			num += child.numRecordsToImport()
		return num

	def numRecordsImported(self):
		num = self.isImported()
		for child in self._children:
			num += child.numRecordsImported()
		return num

	def numBadRecords(self):
		""" Returns total number of bad records in tree model
		"""
		num = int(not self.isValid())
		for child in self._children:
			num += child.numBadRecords()
		return num

	def process(self, dateField, descriptionField, creditField, debitField, currencySign, dateFormat):
		for child in self._children:
			child.process(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)

	def reset(self):
		for child in self._children:
			child.reset()

	def setParent(self, parent):
		self._parent = parent

	def maxColumns(self):
		return max([self.columnCount()] + [child.maxColumns() for child in self._children])

	def appendChild(self, child):
		child.setParent(self)
		self._children.append(child)	

	def child(self, row):
		return self._children[row]

	def children(self):
		return iter(self._children)

	def childCount(self):
		return len(self._children)

	def columnCount(self):
		return 0
		raise NotImplementedError

	def data(self, column, role):
		raise NotImplementedError

	def parent(self):
		return self._parent

	def indexOf(self, child):
		return self._children.index(child)

	def row(self):
		if self._parent:
			return self._parent.indexOf(self)
		return 0

	def canImport(self):
		return False

	def isSelectable(self):
		return False

class CsvFileItem(TreeItem):
	def __init__(self, filename):
		super(CsvFileItem, self).__init__()
		self._filename = filename

	def columnCount(self):
		return 1

	def data(self, column, role):
		if role == QtCore.Qt.DisplayRole and column == 0:
			return QtCore.QVariant(self._filename)
		return QtCore.QVariant()

class CsvRecordItem(TreeItem):
	def __init__(self, rawData):
		super(CsvRecordItem, self).__init__()
		self._rawData = rawData
		self._imported = False
		self._fields = self._csvReader([rawData.data().decode('utf8')]).next()
		self.reset()

	def reset(self):
		self._date = None
		self._desc = None
		self._txDate = None
		self._credit = None
		self._debit = None
		self._error = None
		self._processed = False
		self.data = self._dataFuncRaw

	def checksum(self):
		return QtCore.QString(QtCore.QCryptographicHash.hash(self._rawData, QtCore.QCryptographicHash.Md5).toHex())

	def dataDict(self):
		return {
			'date': 	self._date,
			'desc': 	self._desc,
			'credit': 	self._credit,
			'debit': 	self._debit,
			'txdate': 	self._txDate,
			'raw': 		QtCore.QString.fromUtf8(self._rawData),
			'checksum': self.checksum(),
		}

	def isImported(self):
		return self._imported

	def setImported(self, imported):
		self._imported = imported

	def isSelectable(self):
		return self._processed and self.canImport()

	def canImport(self):
		return self.isValid() and not self._imported

	def _csvReader(self, data):
		# csv.py doesn't do Unicode; encode temporarily as UTF-8:
		for row in csv.reader(self._encoder(data), dialect=csv.excel):
			# decode UTF-8 back to Unicode, cell by cell:
			yield [unicode(cell, 'utf-8') for cell in row]
	
	def _encoder(self, data):
		for line in data:
			yield line.encode('utf-8')

	@property
	def _status(self):
		if self._rawData is None:
			return 'Invalid'
		elif self._error is not None:
			return self._error
		elif self._imported:
			return 'Imported'
		return 'Ready'

	def isValid(self):
		return self._rawData and not self._error

	def columnCount(self):
		if not self._processed:
			return len(self._fields)
		elif self._error:
			return 1
		return 6

	def _dataFuncRaw(self, column, role):
		if role == QtCore.Qt.DisplayRole:
			try:
				return QtCore.QVariant(self._fields[column])
			except IndexError:
				pass
		return QtCore.QVariant()

	def _dataFuncProcessed(self, column, role):

		if role == QtCore.Qt.ForegroundRole:
			if column == enum.kImportColumn_Status:
				if not self.isValid():
					return QtCore.QVariant(QtGui.QColor(255, 0, 0))
				elif self._imported:
					return QtCore.QVariant(QtGui.QColor(255, 165, 0))
				return QtCore.QVariant(QtGui.QColor(0, 255, 0))

		elif role == QtCore.Qt.DisplayRole:
			if column == enum.kImportColumn_Status:
				return QtCore.QVariant(self._status)
			elif column == enum.kImportColumn_Date:
				return QtCore.QVariant(self._date)
			elif column == enum.kImportColumn_TxDate:
				return QtCore.QVariant(self._txDate)
			elif column == enum.kImportColumn_Credit:
				return QtCore.QVariant('%.02f' % self._credit if self._credit else None)
			elif column == enum.kImportColumn_Debit:
				return QtCore.QVariant('%.02f' % abs(self._debit) if self._debit else None)
			elif column == enum.kImportColumn_Description:
				return QtCore.QVariant(self._desc)

		elif role == QtCore.Qt.ToolTipRole:
			return QtCore.QVariant(QtCore.QString.fromUtf8(self._rawData))

		return QtCore.QVariant()

	def process(self, dateIdx, descriptionIdx, creditIdx, debitIdx, currencySign, dateFormat):

		self.reset()

		if not self.isValid():
			return

		try:
			if max(dateIdx, descriptionIdx, creditIdx, debitIdx) > len(self._fields) -1:
				raise DecoderError('Bad Record')

			self._date = self.__getDateField(self._fields[dateIdx], dateFormat)
			self._desc = QtCore.QString(self._fields[descriptionIdx])
			self._txDate = self.__getTransactionDate(self._fields[descriptionIdx], dateIdx)

			if debitIdx == creditIdx:
				amount = self.__getAmountField(self._fields[debitIdx])
				if amount is not None:
					# Use currency multiplier to ensure that credit is +ve (money in),
					# debit -ve (money out)
					amount *= currencySign

					if amount > 0.0:
						self._credit = amount
					else:
						self._debit = amount
			else:
				debitField = self.__getAmountField(self._fields[debitIdx])
				creditField = self.__getAmountField(self._fields[creditIdx])
				self._debit = abs(debitField) * -1.0 if debitField else None
				self._credit = abs(creditField) if creditField else None

			if not self._debit and not self._credit:
				raise DecoderError('No credit or debit found')

		except DecoderError, exc:
			self._error = str(exc)

		finally:
			self._processed = True
			self.data = self._dataFuncProcessed

	def __getAmountField(self, field):
		""" Extract and return amount (double). If a simple conversion doesn't
			succeed, then try and parse the string to remove any currency sign
			or other junk.

			Returns None if field does not contain valid double.
		"""

		# Get rid of commas from amount field and try and covert to double
		field = field.replace(',', '')
		value, ok = QtCore.QVariant(field).toDouble()

		if not ok:
			# Probably has currency sign - extract all valid currency characters
			match = re.search('([\d\-\.]+)', field)
			if match:
				value, ok = QtCore.QVariant(match.group(1)).toDouble()

		if ok:
			return value

		return None

	def __getTransactionDate(self, field, dateField):
		""" Try and extract a transaction date from the description field.
			Value format are ddMMMyy hhmm, ddMMMyy and ddMMM. 
			When the year is not available (or 2 digits) then the value validated date field
			is used
		"""
		timeDate = None

		#Format is "23DEC09 1210"
		rx = QtCore.QRegExp('(\\d\\d[A-Z]{3}\\d\\d \\d{4})')
		if rx.indexIn(field) != -1:
			timeDate = QtCore.QDateTime.fromString (rx.cap(1), "ddMMMyy hhmm").addYears(100)

		if timeDate is None:
			# Format is "06NOV10"
			rx = QtCore.QRegExp('(\\d{2}[A-Z]{3}\\d{2})')
			if rx.indexIn(field) != -1:
				timeDate = QtCore.QDateTime.fromString (rx.cap(1), "ddMMMyy").addYears(100)

		# Format is " 06NOV" <- note the stupid leading blank space..
		if timeDate is None:
			rx = QtCore.QRegExp(' (\\d\\d[A-Z]{3})')
			if rx.indexIn(field) != -1:
				# Add the year from date field to the transaction date
				timeDate = QtCore.QDateTime.fromString (rx.cap(1) + dateField.toString("yyyy"), "ddMMMyyyy")

		if timeDate is not None and timeDate.isValid():
			return timeDate

	def __getDateField(self, field, dateFormat):
		""" Extract date field using supplied format 
		"""
		date = QtCore.QDate.fromString(field, dateFormat)

		if not date.isValid():
			raise DecoderError('Invalid date: %r' % field)

		return date


class TreeModel(QtCore.QAbstractItemModel):
	#importChanged = QtCore.pyqtSignal(int)

	def __init__(self, files, parent=None):
		super(TreeModel, self).__init__(parent=parent)
		self._headers = []
		self._root = TreeItem()
		self._checksums = []
		self.__currentTimestamp = None
		self.dataSaved = False

		# Import all record checksums
		query = QtSql.QSqlQuery('SELECT checksum from records where userid=%d' % db.userId)
		if query.lastError().isValid():
			raise Exception(query.lastError().text())

		while query.next():
			self._checksums.append(query.value(0).toString())

		for item in self.readFiles(files):
			self._root.appendChild(item)

		self._numColumns = self._root.maxColumns()
		self._headers = range(self._numColumns)

	def reset(self):
#		self.__records = deepcopy(self.__recordsRollback)
		self._root.reset()
		self.dataSaved = False
		self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount() -1, self.columnCount() - 1))
		self.__currentTimestamp = None

	def numRecordsToImport(self):
		return self._root.numRecordsToImport()

	def numBadRecords(self):
		return self._root.numBadRecords()

	def numRecordsImported(self):
		return self._root.numRecordsImported()

	def accountChanged(self, accountData):
		""" Account selection has changed

			Get settings for the account and create new model to decode the data
		"""
		with utils.showWaitCursor():
			if accountData is None:
				self._root.reset()
				self._headers = range(self._root.maxColumns())
			else:
				dateField, descriptionField, creditField, debitField, currencySign, dateFormat = accountData
				self._root.process(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)
				self._headers = ['Status', 'Date', 'Tx Date', 'Credit', 'Debit', 'Description']

		self._numColumns = self._root.maxColumns()
		self.modelReset.emit()

	def saveRecord(self, accountId, index):
		""" Saves the import record to the database
			Raises ImportException on error
		"""
		item = self.getNodeItem(index)
		rec = item.dataDict()

		# Ensure we record the same timestamp for this import
		self.__currentTimestamp = self.__currentTimestamp or QtCore.QDateTime.currentDateTime()

		query = QtSql.QSqlQuery()
		query.prepare("""
				INSERT INTO records
				(date, userid, accounttypeid, description, txdate, amount, insertdate, rawdata, checksum)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			""")

		query.addBindValue(rec['date'])
		query.addBindValue(db.userId)
		query.addBindValue(accountId)
		query.addBindValue(rec['desc'])
		query.addBindValue(rec['txdate'])
		query.addBindValue(rec['credit'] or rec['debit'])
		query.addBindValue(self.__currentTimestamp)
		query.addBindValue(rec['raw'])
		query.addBindValue(rec['checksum'])

		query.exec_()

		if query.lastError().isValid():
			raise ImportException(query.lastError().text())

		item.setImported(True)
		self.dataSaved = True

		# Tell the view our data has changed
		self.dataChanged.emit(
				self.createIndex(index.row(), 0, item), 
				self.createIndex(index.row(), self.columnCount() - 1, item),
			)

	def getNodeItem(self, index):
		if index.isValid():
			return index.internalPointer()

		return self._root

	def checksum(self, data):
		return QtCore.QString(QtCore.QCryptographicHash.hash(data, QtCore.QCryptographicHash.Md5).toHex())

	def readFiles(self, files):
		for filename in files:
			item = CsvFileItem(filename)
			csvfile = QtCore.QFile(filename)

			if not csvfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
				raise Exception('Cannot open file %r' % filename)

			i = 0
			while not csvfile.atEnd():
				i += 1
				rawData = csvfile.readLine().trimmed()
				recItem = CsvRecordItem(rawData)

				if self.checksum(rawData) in self._checksums or (i % 3):
					recItem.setImported(True)

				item.appendChild(recItem)

			yield item

	def columnCount(self, parent=QtCore.QModelIndex()):
		return self._numColumns

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		item = self.getNodeItem(index)
		return item.data(index.column(), role)

	def flags(self, index):
		""" Only allow selection on records that can be imported
		"""
		if not index.isValid():
			return 0

		if self.getNodeItem(index).isSelectable():
			return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

		return QtCore.Qt.ItemIsEnabled

	def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
		if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
			try:
				return self._headers[section]
			except IndexError:
				pass
			 
		return QtCore.QVariant()

	def index(self, row, column, parent=QtCore.QModelIndex()):

		if not self.hasIndex(row, column, parent):
			return QtCore.QModelIndex()

		parentItem = self.getNodeItem(parent)
		childItem = parentItem.child(row)

		if childItem:
			return self.createIndex( row, column, childItem)

		return QtCore.QModelIndex()

	def parent(self, index):

		if not index.isValid():
			return QtCore.QModelIndex()

		childItem = self.getNodeItem(index)
		parentItem = childItem.parent()

		if parentItem == self._root:
			return QtCore.QModelIndex()

		return self.createIndex(parentItem.row(), 0, parentItem)

	def rowCount(self, parent=QtCore.QModelIndex()):

		if parent.column() > 0:
			return 0

		item = self.getNodeItem(parent)
		return item.childCount()

def resizeColumns(index):
	if not index.isValid():
		return
	item = index.internalPointer()
	print item.columnCount()
	for column in xrange(item.columnCount()):
		print column

def main():
	app = QtGui.QApplication(sys.argv)
	model = TreeModel(['test1.csv', 'test2.csv', 'test3.csv'])

	widget = QtGui.QWidget()
	layout = QtGui.QVBoxLayout()
	combo = QtGui.QComboBox()
	combo.addItem('Raw')
	combo.addItem('Account1')
	combo.addItem('Account2')
	combo.addItem('Account3')
	layout.addWidget(combo)

	tree = QtGui.QTreeView()
#	tree.expanded.connect(resizeColumns)
	tree.setModel(model)
	
	tree.expandAll()
	
	layout.addWidget(tree)
	combo.currentIndexChanged.connect(model.accountChanged)
	model.modelReset.connect(tree.expandAll)

	widget.setLayout(layout)
	widget.show()

	return app.exec_()

if __name__ == "__main__":
	import sys
	sys.exit(main())
