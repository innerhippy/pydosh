from PyQt4 import QtGui, QtCore
QtCore.pyqtRemoveInputHook()
import pdb
import sys
import re

import csv
import enum
import utils
from dialogs import unicode_csv_reader

class DecoderError(Exception):
	""" General Decoder exceptions
	"""

class TreeItem(object):
	def __init__(self):
		super(TreeItem, self).__init__()
		self._parent = None
		self._children = []

	def process(self, dateField, descriptionField, creditField, debitField, currencySign, dateFormat):
		for child in self._children:
			child.process(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)

	def setParent(self, parent):
		self._parent = parent

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
		raise NotImplementedError

	def data(self, column):
		raise NotImplementedError

	def parent(self):
		return self._parent

	def indexOf(self, child):
		return self._children.index(child)

	def row(self):
		if self._parent:
			return self._parent.indexOf(self)
		return 0

class CsvFileItem(TreeItem):
	def __init__(self, filename):
		super(CsvFileItem, self).__init__()
		self._filename = filename

	def columnCount(self):
		return 1

	def data(self, column):
		if column == 0:
			return QtCore.QVariant(self._filename)
		return QtCore.QVariant()

class CsvRecordItem(TreeItem):
	def __init__(self, rawData):
		super(CsvRecordItem, self).__init__()
		self._rawData = rawData
		self._fields = self._csvReader([rawData.data().decode('utf8')]).next()
		self._imported = False
		self._date = None
		self._desc = None
		self._txDate = None
		self._credit = None
		self._debit = None
		self._error = None
		self._processed = False

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
			return 'Error'
		elif self._imported:
			return 'Imported'
		return 'Ready'

	def setImported(self, imported):
		self._imported = imported

	def isValid(self):
		return self._rawData and not self._error

	def columnCount(self):
		if self._processed == False:
			return len(self._fields)
		elif self._error:
			return 1
		return 5

	def data(self, column):
		if self._processed:
			if self._error is None:
				if column == enum.kImportColumn_Status:
					return QtCore.QVariant(self._status)
				elif column == enum.kImportColumn_Date:
					return QtCore.QVariant(self._date)
				elif column == enum.kImportColumn_TxDate:
					return QtCore.QVariant(self._txDate)
				elif column == enum.kImportColumn_Credit:
					return QtCore.QVariant(self._credit)
				elif column == enum.kImportColumn_Debit:
					return QtCore.QVariant(self._debit)
				elif column == enum.kImportColumn_Description:
					return QtCore.QVariant(self._desc)
			elif column == 0:
				return QtCore.QVariant(self._error)
		else:
			try:
				return QtCore.QVariant(self._fields[column])
			except IndexError:
				pass

		return QtCore.QVariant()

	def process(self, dateIdx, descriptionIdx, creditIdx, debitIdx, currencySign, dateFormat):

		if not self.isValid():
			return
		try:
			if max(dateIdx, descriptionIdx, creditIdx, debitIdx) > len(self._fields) -1:
				raise DecoderError('Bad Record')

			self._date = self.__getDateField(self._fields[dateIdx], dateFormat)
			self._desc = self._fields[descriptionIdx]
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
		else:
			self._processed = True

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
	def __init__(self, files, parent=None):
		super(TreeModel, self).__init__(parent=parent)
		self._numColumns = 0
		self._root = TreeItem()
		self._checksums = [
			'a045b8caa4bb7e7cc9ec7c2bca830f52',
			'6b6b3bdfe23fcfed5708aa75a6b95c3c',
			'229370b92c6aec07e81c2a7a8c60af0b',
			'2b2ec49808ec4445fd22bcc5620688c9',
			'0114272edba182214663366bc98c8334',
			'ead9afb89739518e70667a602905f7fb'
		]

		for item in self.readFiles(files):
			self._root.appendChild(item)

	def setAccountType(self, index):
		""" Account selection has changed

			Get settings for the account and create new model to decode the data
		"""
		dateField = 0
		descriptionField = 1
		creditField = 2
		debitField = 3
		currencySign = 1
		dateFormat = 'dd/MM/yyyy'

		with utils.showWaitCursor():
			self._root.process(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)

		self.modelReset.emit()


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

			while not csvfile.atEnd():
				rawData = csvfile.readLine().trimmed()
				recItem = CsvRecordItem(rawData)
				if self.checksum(rawData) in self._checksums:
					recItem.setImported(True)
				self._numColumns = max(self._numColumns, recItem.columnCount())
				item.appendChild(recItem)
			yield item

	def columnCount(self, parent=QtCore.QModelIndex()):
		return self._numColumns

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		item = self.getNodeItem(index)
		if isinstance(item, CsvRecordItem):
			if role == QtCore.Qt.ForegroundRole:
#			if item.column() == 0:
#				if not self.__records[item.row()].valid:
#					return QtCore.QVariant(QtGui.QColor(255, 0, 0))
#				elif self.__records[item.row()].imported:
#					return QtCore.QVariant(QtGui.QColor(255, 165, 0))
#				return QtCore.QVariant(QtGui.QColor(0, 255, 0))

		if role != QtCore.Qt.DisplayRole:
			return QtCore.QVariant()

		if index.column() == 0:
#			pdb.set_trace()
			print item.data(0).toString()

		return item.data(index.column())

	def flags(self, index):
		if not index.isValid():
			return 0

		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

	def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
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

def main():
	app = QtGui.QApplication(sys.argv)
	model = TreeModel(['test1.csv', 'test2.csv', 'test3.csv'])

	widget = QtGui.QWidget()
	layout = QtGui.QVBoxLayout()
	combo = QtGui.QComboBox()
	combo.addItem('account1')
	combo.addItem('account2')
	combo.addItem('account3')
	layout.addWidget(combo)

	tree = QtGui.QTreeView()
	tree.setModel(model)
	tree.expandAll()
	layout.addWidget(tree)
	combo.currentIndexChanged.connect(model.setAccountType)
	model.modelReset.connect(tree.expandAll)

	widget.setLayout(layout)
	widget.show()

	return app.exec_()

if __name__ == "__main__":
	import sys
	sys.exit(main())
