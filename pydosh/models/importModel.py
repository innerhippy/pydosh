import re
import os
import csv
import hashlib
import codecs
from PySide import QtCore, QtGui, QtSql

from pydosh import currency, utils, enum
from pydosh.database import db
import pydosh.pydosh_rc

class DecoderError(Exception):
	""" General Decoder exceptions
	"""

class ImportException(Exception):
	""" General exception for record import
	"""

class TreeItem(object):
	def __init__(self):
		super(TreeItem, self).__init__()
		self._parent = None
		self._error = None
		self._imported = False
		self._duplicate = False
		self._children = []

	def isValid(self):
		return True

	def setImported(self, imported):
		pass

	def setDuplicate(self, duplicate):
		pass

	def checksum(self):
		return None

	def numRecordsToImport(self):
		""" Returns the number of records left that can be imported
		"""
		num = 1 if self.canImport() else 0
		for child in self._children:
			num += child.numRecordsToImport()
		return num

	def setRecordsImported(self, checksums):
		checksum = self.checksum()

		if checksum is not None:
			self.setImported(checksum in checksums)

		for child in self._children:
			child.setRecordsImported(checksums)

	def setDuplicateRecords(self, checksums=None):
		checksum = self.checksum()

		if checksums is None:
			checksums = set()

		if checksum is not None:
			self.setDuplicate(checksum in checksums)
			checksums.add(checksum)

		for child in self._children:
			child.setDuplicateRecords(checksums)

	def numRecordsImported(self):
		num = int(self._imported)
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

	def formatItem(self, dateField, descriptionField, creditField, debitField, currencySign, dateFormat):
		for child in self._children:
			child.formatItem(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)

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
			return os.path.basename(self._filename)

class CsvRecordItem(TreeItem):
	def __init__(self, rawData):
		super(CsvRecordItem, self).__init__()
		self._date = None
		self._desc = None
		self._credit = None
		self._debit = None
		self._error = None
		self._formatted = False
		self._rawData = rawData
		self._fields = self._csvReader([rawData]).next()
		self.reset()

	def reset(self):
		self._setFormatted(False)

	def _setFormatted(self, formatted):
		self._formatted = formatted
		self.data = self._dataFuncProcessed if formatted else self._dataFuncRaw

	def checksum(self):
		return hashlib.md5(self._rawData.encode('utf-8')).hexdigest()

	def dataDict(self):
		return {
			'date': 	self._date,
			'desc': 	self._desc,
			'credit': 	self._credit,
			'debit': 	self._debit,
			'raw': 		self._rawData,
			'checksum': self.checksum(),
		}

	def setImported(self, imported):
		self._imported = imported

	def setDuplicate(self, duplicate):
		self._duplicate = duplicate

	def isSelectable(self):
		return self._formatted and self.canImport()

	def canImport(self):
		return self.isValid() and not self._imported and not self._duplicate

	def _csvReader(self, data):
		# csv.py doesn't do Unicode; encode temporarily as UTF-8:
		for row in csv.reader(self._encoder(data), dialect=csv.excel):
			# decode UTF-8 back to Unicode, cell by cell:
			yield [unicode(cell, 'utf-8') for cell in row]

	def _encoder(self, data):
		for line in data:
			yield line.encode('utf-8')

	@property
	def _statusAsText(self):
		""" Property to get the status description
		"""
		if self._rawData is None:
			return 'Invalid'
		elif self._error is not None:
			return self._error
		elif self._imported:
			return 'Imported'
		elif self._duplicate:
			return 'Duplicate'

		return 'Ready'

	def isValid(self):
		""" True if we have valid raw data and no error
		"""
		return self._rawData and not self._error

	def columnCount(self):
		if not self._formatted:
			return len(self._fields)
		elif self._error:
			return 1
		return 6

	def _dataFuncRaw(self, column, role):
		if role == QtCore.Qt.DisplayRole:
			try:
				return self._fields[column]
			except IndexError:
				pass

	def _dataFuncProcessed(self, column, role):

		if role == QtCore.Qt.ForegroundRole:
			if column == enum.kImportColumn_Status:
				if not self.isValid():
					return QtGui.QColor(255, 0, 0)
				elif self._imported:
					return QtGui.QColor(255, 165, 0)
				elif self._duplicate:
					return QtGui.QColor(255, 165, 0)
				return QtGui.QColor(0, 255, 0)

		elif role == QtCore.Qt.DisplayRole:
			if column == enum.kImportColumn_Status:
				return self._statusAsText
			elif column == enum.kImportColumn_Date:
				return self._date
			elif column == enum.kImportColumn_Credit:
				return '%.02f' % self._credit if self._credit else None
			elif column == enum.kImportColumn_Debit:
				return '%.02f' % abs(self._debit) if self._debit else None
			elif column == enum.kImportColumn_Description:
				return self._desc

		elif role == QtCore.Qt.ToolTipRole:
			return self._rawData

	def formatItem(self, dateIdx, descriptionIdx, creditIdx, debitIdx, currencySign, dateFormat):

		self._date = None
		self._desc = None
		self._credit = None
		self._debit = None
		self._error = None

		if not self.isValid():
			return

		try:
			if max(dateIdx, descriptionIdx, creditIdx, debitIdx) > len(self._fields) -1:
				raise DecoderError('Bad Record')

			self._date = self.__getDateField(self._fields[dateIdx], dateFormat)
			self._desc = self._fields[descriptionIdx]

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
			self._setFormatted(True)

	def __getAmountField(self, field):
		""" Extract and return amount from str type to double. 
			If a simple conversion doesn't succeed, then try and parse 
			the string to remove any currency sign or other junk.

			Returns None if field does not contain valid double.
		"""
		value = None
		field = field.replace(',', '')

		# Get rid of commas from amount field and try and covert to double
		try:
			value = float(field)
		except ValueError:
			# Probably has currency sign - extract all valid currency characters
			match = re.search('([\d\-\.]+)', field)
			if match:
				try:
					value = float(match.group(1))
				except ValueError:
					pass

		return value

	def __getDateField(self, field, dateFormat):
		""" Extract date field using supplied format
		"""
		date = QtCore.QDate.fromString(field, dateFormat)

		if not date.isValid():
			raise DecoderError('Invalid date: %r' % field)

		return date

class ImportModel(QtCore.QAbstractItemModel):

	def __init__(self, files, parent=None):
		super(ImportModel, self).__init__(parent=parent)
		self._headers = []
		self._root = TreeItem()
		self._checksums = []
		self._checksumsSaved = None
		self.__currentTimestamp = None

		# Import all record checksums
		query = QtSql.QSqlQuery('SELECT checksum FROM records WHERE userid=%d' % db.userId)
		if query.lastError().isValid():
			raise Exception(query.lastError().text())

		while query.next():
			self._checksums.append(query.value(0))

		self._checksumsSaved = self._checksums[:]

		for item in self.readFiles(files):
			self._root.appendChild(item)

		self._root.setRecordsImported(self._checksums)
		self._root.setDuplicateRecords()

		self._numColumns = self._root.maxColumns()
		self._headers = range(self._numColumns)

	def reset(self):
		self._checksums = self._checksumsSaved[:]
		self.beginResetModel()
		self._root.setRecordsImported(self._checksums)
		self.endResetModel()
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
		self.beginResetModel()
		with utils.showWaitCursor():
			if accountData is None:
				self._root.reset()
				self._headers = range(self._root.maxColumns())
			else:
				dateField, descriptionField, creditField, debitField, currencySign, dateFormat = accountData
				self._root.formatItem(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)
				self._headers = ['Status', 'Date', 'Credit', 'Debit', 'Description']

		self._numColumns = self._root.maxColumns()

		self.endResetModel()

	def saveRecord(self, accountId, currencyCode, index):
		""" Saves the import record to the database
			Raises ImportException on error
		"""
		item = self.getNodeItem(index)
		rec = item.dataDict()

		# Ensure we record the same timestamp for this import
		self.__currentTimestamp = self.__currentTimestamp or QtCore.QDateTime.currentDateTime()

		query = QtSql.QSqlQuery()
		query.prepare("""
			INSERT INTO records (date, userid, accounttypeid,
								 description, amount, insertdate,
								 rawdata, checksum, currency)
						 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
		""")

		query.addBindValue(rec['date'])
		query.addBindValue(db.userId)
		query.addBindValue(accountId)
		query.addBindValue(rec['desc'])
		query.addBindValue(rec['credit'] or rec['debit'])
		query.addBindValue(self.__currentTimestamp)
		query.addBindValue(rec['raw'])
		query.addBindValue(rec['checksum'])
		query.addBindValue(currencyCode)

		query.exec_()

		if query.lastError().isValid():
			raise ImportException(query.lastError().text())

		self._checksums.append(rec['checksum'])
		item.setImported(True)
		self.dataChanged.emit(index, index)

	def getNodeItem(self, index):
		if index.isValid():
			return index.internalPointer()

		return self._root

	def readFiles(self, files):
		for filename in files:
			item = CsvFileItem(filename)
			with codecs.open(filename, 'rb', 'UTF-8') as f:
				for line in f:
					recItem = CsvRecordItem(line.strip())
					item.appendChild(recItem)
			yield item

	def columnCount(self, parent=QtCore.QModelIndex()):
		return self._numColumns

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid():
			return None

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

		return None

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


