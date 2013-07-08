from PyQt4 import QtGui, QtCore
QtCore.pyqtRemoveInputHook()
import pdb
import sys

import utils
from dialogs import unicode_csv_reader

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

#	def children(self):
#		return iter(self._children)

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
			return self._filename
		return QtCore.QVariant()

class ImportRecord(object):
	def __init__(self, *args):
		super(ImportRecord, self).__init__()
		self.data, self.date, self.desc, self.txdate, self.debit, self.credit, self.error = args
		self.__isImported = False

	@property
	def valid(self):
		return self.error is None

	@property
	def imported(self):
		return self.__isImported

	@imported.setter
	def imported(self, value):
		self.__isImported = value

	@property
	def checksum(self):
		return QtCore.QString(QtCore.QCryptographicHash.hash(self.data, QtCore.QCryptographicHash.Md5).toHex())

	def __eq__(self, other):
		return self.checksum == other.checksum

	def __str__(self):
		return 'date=%r txdate=%r debit=%r credit=%r desc=%r' % (self.date, self.txdate, self.credit, self.debit, self.desc)

	def __repr__(self):
		return '%r' % str(self)


class CsvRecordItem(TreeItem):
	def __init__(self, rawData):
		super(CsvRecordItem, self).__init__()
		self._rawData = rawData
		self._fields = unicode_csv_reader([rawData.data().decode('utf8')]).next()
		self._date = None
		self._desc = None
		self._txDate = None
		self._credit = None
		self._debit = None
		self._error = None

	def isValid(self):
		return self._rawData and not self._error

	def columnCount(self):
		return len(self._fields)

	def data(self, column):
		try:
			return self._fields[column]
		except IndexError:
			return QtCore.QVariant()

	def process(self, dateIdx, descriptionIdx, creditIdx, debitIdx, currencySign, dateFormat):
		if not self.isValid():
			return

		try:
			if max(dateIdx, descriptionIdx, creditIdx, debitIdx) > len(self._fields) -1:
				raise DecoderError('Bad Record')

			self._date = self.__getDateField(self._fields[dateIdx], dateFormat)

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
		dateFormat = 'dd/MM/yyy'

#		model = ImportModel(self)
#		db.commit.connect(model.save)
#		db.rollback.connect(model.reset)

		with utils.showWaitCursor():
			self._root.process(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)

		return
		if True:
			records = self.__processRecords(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)
			model.loadRecords(records)

			proxy = QtGui.QSortFilterProxyModel(model)
			proxy.setSourceModel(model)
			proxy.setFilterKeyColumn(0)

			self.view.setModel(proxy)
			self.view.verticalHeader().hide()
			self.view.setSortingEnabled(True)
			self.view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
			self.view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
			self.view.horizontalHeader().setStretchLastSection(True)
			self.view.sortByColumn(0, QtCore.Qt.AscendingOrder)
			self.view.resizeColumnsToContents()
			self.view.selectionModel().selectionChanged.connect(self.__recordsSelected)
			self.importCancelButton.setEnabled(False)
			self.selectAllButton.setEnabled(bool(model.numRecordsToImport()))
			self.__setCounters()

		# Hide txDate colum if we don't need it
		for row in xrange(model.rowCount()):
			if model.index(row, enum.kImportColumn_TxDate).data().isValid():
				self.view.setColumnHidden(enum.kImportColumn_TxDate, False)
				break
		else:
			self.view.setColumnHidden(enum.kImportColumn_TxDate, True)

	def __processRecords(self, dateIdx, descriptionIdx, creditIdx, debitIdx, currencySign, dateFormat):
		""" Generator to decode the raw csv data according to the account configuration.
			Yields record containing verified data ready to be saved to database
		"""

		for filename, rawRecords in self.__rawData.iteritems():
			for lineno, rawdata in enumerate(rawRecords):

				if not rawdata:
					continue

				dateField = descField = txDate = debitField = creditField = None
				row = unicode_csv_reader([rawdata.data().decode('utf8')]).next()

				try:
					if max(dateIdx, descriptionIdx, creditIdx, debitIdx) > len(row) -1:
						raise DecoderError('Bad record')

					dateField  = self.__getDateField(row[dateIdx], dateFormat)
					descField  = row[descriptionIdx]
					txDate     = self.__getTransactionDate(row[descriptionIdx], dateField)

					if debitIdx == creditIdx:
						amount = self.__getAmountField(row[debitIdx])
						if amount is not None:
							# Use currency multiplier to ensure that credit is +ve (money in),
							# debit -ve (money out)
							amount *= currencySign

							if amount > 0.0:
								creditField = amount
							else:
								debitField = amount
					else:
						debitField = self.__getAmountField(row[debitIdx])
						creditField = self.__getAmountField(row[creditIdx])
						debitField = abs(debitField) * -1.0 if debitField else None
						creditField = abs(creditField) if creditField else None

					if not debitField and not creditField:
						raise DecoderError('No credit or debit found')

				except DecoderError, exc:
					error = '%s[%d]: %r' % (QtCore.QFileInfo(filename).fileName(), lineno, str(exc))
					yield (rawdata, dateField, descField, txDate, debitField, creditField, error,)

				except Exception, exc:
					QtGui.QMessageBox.critical(
						self, 'Import Error', str(exc),
						QtGui.QMessageBox.Ok)

				else:
					yield (rawdata, dateField, descField, txDate, debitField, creditField, None,)

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


	def getNodeItem(self, index):
		if index.isValid():
			return index.internalPointer()
		return self._root

	def readFiles(self, files):
		for filename in files:
			item = CsvFileItem(filename)
			csvfile = QtCore.QFile(filename)

			if not csvfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
				raise Exception('Cannot open file %r' % filename)

			while not csvfile.atEnd():
				rawData = csvfile.readLine().trimmed()
				recItem = CsvRecordItem(rawData)
				self._numColumns = max(self._numColumns, recItem.columnCount())
				item.appendChild(recItem)
			yield item

	def columnCount(self, parent=QtCore.QModelIndex()):
		return self._numColumns

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		if role != QtCore.Qt.DisplayRole:
			return QtCore.QVariant()

		item = self.getNodeItem(index)
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
	model = TreeModel(['test1.csv', 'test2.csv'])

	widget = QtGui.QWidget()
	layout = QtGui.QVBoxLayout()
	combo = QtGui.QComboBox()
	combo.addItem('account1')
	combo.addItem('account2')
	combo.addItem('account3')
	layout.addWidget(combo)

	tree = QtGui.QTreeView()
	tree.setModel(model)
	layout.addWidget(tree)
	combo.currentIndexChanged.connect(model.setAccountType)

	widget.setLayout(layout)
	widget.show()

	return app.exec_()

if __name__ == "__main__":
	import sys
	sys.exit(main())
