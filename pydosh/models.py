from exceptions import ImportException
from PyQt4 import QtCore, QtGui, QtSql
import enum
import csv
from database import db
import utils
import pydosh_rc

import pdb

class DecoderError(Exception):
	""" General Decoder exceptions
	"""

class ImportException(Exception):
	""" General exception for record import
	"""

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
		self._imported = False
		self._children = []

	def isValid(self):
		return True

	def setImported(self, imported):
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
			return QtCore.QVariant(QtCore.QFileInfo(self._filename).fileName())
		return QtCore.QVariant()

class CsvRecordItem(TreeItem):
	def __init__(self, rawData):
		super(CsvRecordItem, self).__init__()
		self._date = None
		self._desc = None
		self._txDate = None
		self._credit = None
		self._debit = None
		self._error = None
		self._rawData = rawData
		self._fields = self._csvReader([rawData.data().decode('utf8')]).next()
		self.reset()


	def reset(self):
		self._setFormatted(False)
		return
		self._date = None
		self._desc = None
		self._txDate = None
		self._credit = None
		self._debit = None
		self._error = None
		self._formatted = False

	def _setFormatted(self, formatted):
		self._formatted = formatted
		self.data = self._dataFuncProcessed if formatted else self._dataFuncRaw

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

	def setImported(self, imported):
		self._imported = imported

	def isSelectable(self):
		return self._formatted and self.canImport()

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
		if not self._formatted:
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

	def formatItem(self, dateIdx, descriptionIdx, creditIdx, debitIdx, currencySign, dateFormat):

#		self.reset()
		self._date = None
		self._desc = None
		self._txDate = None
		self._credit = None
		self._debit = None
		self._error = None

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
			self._setFormatted(True)


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


class ImportModel(QtCore.QAbstractItemModel):
	#importChanged = QtCore.pyqtSignal(int)

	def __init__(self, files, parent=None):
		super(ImportModel, self).__init__(parent=parent)
		self._headers = []
		self._root = TreeItem()
		self._checksums = []
		self._checksumsSaved = None
		self.__currentTimestamp = None

		# Import all record checksums
		query = QtSql.QSqlQuery('SELECT checksum from records where userid=%d' % db.userId)
		if query.lastError().isValid():
			raise Exception(query.lastError().text())

		while query.next():
			self._checksums.append(query.value(0).toString())

		self._checksumsSaved = self._checksums[:]

		for item in self.readFiles(files):
			self._root.appendChild(item)

		self._root.setRecordsImported(self._checksums)

		self._numColumns = self._root.maxColumns()
		self._headers = range(self._numColumns)

	def reset(self):
		self._checksums = self._checksumsSaved[:]
#		self._root.reset()
		#self.beginResetModel()
		self._root.setRecordsImported(self._checksums)
		self.__currentTimestamp = None
		#self.endResetModel()
		#super(ImportModel, self).reset()
		
#		self.dataChanged.emit(
#			self.createIndex(0, 0), 
#			self.createIndex(self.rowCount() -1, self.columnCount() - 1)
#		)

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
				self._headers = ['Status', 'Date', 'Tx Date', 'Credit', 'Debit', 'Description']

		self._numColumns = self._root.maxColumns()

		self.endResetModel()

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

		self._checksums.append(rec['checksum'])
		item.setImported(True)
		self.dataChanged.emit(index, index)

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



class RecordModel(QtSql.QSqlTableModel):
	def __init__(self, parent=None):
		super(RecordModel, self).__init__(parent=parent)
		self._highlightText = None

	def select(self):
		status = super(RecordModel, self).select()
		while self.canFetchMore():
			self.fetchMore()

		return status

	def flags(self, index):
		flags = super(RecordModel, self).flags(index)
		if index.column() == enum.kRecordColumn_Checked:
			return flags | QtCore.Qt.ItemIsUserCheckable
		return flags

	def selectStatement(self):
		if self.tableName().isEmpty():
			return QtCore.QString()

		queryFilter = self.filter()
		queryFilter = 'WHERE ' + queryFilter if queryFilter else ''

		query = """
                SELECT r.recordid,
                       r.checked,
                       array_to_string(array_agg(t.tagname ORDER BY t.tagname), ','),
                       r.checkdate,
                       r.date,
                       r.accounttypeid,
                       at.accountname,
                       r.description,
                       r.txdate,
                       r.amount,
                       r.insertdate,
                       r.rawdata
                  FROM records r
            INNER JOIN accounttypes at ON at.accounttypeid=r.accounttypeid
                   AND r.userid=%(userid)s
             LEFT JOIN recordtags rt ON rt.recordid=r.recordid
             LEFT JOIN tags t ON rt.tagid=t.tagid
                       %(filter)s
              GROUP BY r.recordid, at.accountname
              ORDER BY r.date, r.recordid
		""" % {'userid': db.userId, 'filter': queryFilter}

		return query

	def deleteRecords(self, indexes):
		recordIds = [self.index(index.row(), enum.kRecordColumn_RecordId).data().toPyObject() for index in indexes]
		query = QtSql.QSqlQuery("""
            DELETE FROM records
                  WHERE recordid in (%s)
		""" % ','.join(str(rec) for rec in recordIds))

		if query.lastError().isValid():
			return False

		self.select()
		self.dataChanged.emit(indexes[0], indexes[-1])

		return True

	def highlightText(self, text):
		self._highlightText = text
		self.reset()

	def data(self, item, role=QtCore.Qt.DisplayRole):
		""" Return data from the model, formatted for viewing
		"""
		if not item.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.CheckStateRole:
			if item.column() == enum.kRecordColumn_Checked:
				if super(RecordModel, self).data(item).toBool():
					return QtCore.QVariant(QtCore.Qt.Checked)
				else:
					return QtCore.QVariant(QtCore.Qt.Unchecked)

		elif role == QtCore.Qt.FontRole:
			if item.column() == enum.kRecordColumn_Description:
				if self._highlightText and item.data(QtCore.Qt.DisplayRole).toString().contains(self._highlightText, QtCore.Qt.CaseInsensitive):
					font = QtGui.QFont()
					font.setBold(True)
					return QtCore.QVariant(font)

		elif role == QtCore.Qt.ToolTipRole:
			if item.column() == enum.kRecordColumn_Tags:
				# Show tag names for this record
				return item.data(QtCore.Qt.UserRole)

			elif item.column() == enum.kRecordColumn_Checked:
				if item.data(QtCore.Qt.CheckStateRole).toPyObject() == QtCore.Qt.Checked:
					text = "Checked: " + super(RecordModel, self).data(
						self.index(item.row(), enum.kRecordColumn_CheckDate)).toDateTime().toString("dd/MM/yy hh:mm")
					return QtCore.QVariant(text)

			elif item.column() == enum.kRecordColumn_Date:
				# Show when the record was imported
				text = "Imported: " + super(RecordModel, self).data(
					self.index(item.row(), enum.kRecordColumn_InsertDate)).toDateTime().toString("dd/MM/yy hh:mm")
				return QtCore.QVariant(text)

			elif item.column() == enum.kRecordColumn_Description:
				# Full, raw text
				return super(RecordModel, self).data(item, QtCore.Qt.DisplayRole)

		elif role == QtCore.Qt.UserRole:
			if item.column() == enum.kRecordColumn_Tags:
				# Tags as comma separated string (from database)
				tags = super(RecordModel, self).data(item, QtCore.Qt.DisplayRole)
				return tags if tags.toString() else QtCore.QVariant()

			elif item.column() == enum.kRecordColumn_Amount:
				# Raw data - signed amount
				return super(RecordModel, self).data(item, QtCore.Qt.DisplayRole)

		elif role == QtCore.Qt.ForegroundRole:	
			if item.column() == enum.kRecordColumn_Amount:
				# Indicate credit/debit with colour
				if item.data(QtCore.Qt.UserRole).toPyObject() > 0.0:
					return QtCore.QVariant(QtGui.QColor(0, 255, 0))
				else:
					return QtCore.QVariant(QtGui.QColor(255, 0, 0))

		elif role == QtCore.Qt.DecorationRole:
			if item.column() == enum.kRecordColumn_Tags:
				# Show tag icon if we have any
				if item.data(QtCore.Qt.UserRole).toString():
					return QtCore.QVariant(QtGui.QIcon(':/icons/tag_yellow.png'))

		elif role == QtCore.Qt.DisplayRole:
			if item.column() in (enum.kRecordColumn_Checked, enum.kRecordColumn_Tags):
				# Don't display anything for these fields
				return QtCore.QVariant()

			elif item.column() == enum.kRecordColumn_Amount:
				# Display absolute currency values. credit/debit is indicated by background colour
				return QtCore.QVariant('%.02f' % abs(super(RecordModel, self).data(item).toPyObject()))

			elif item.column() == enum.kRecordColumn_Description:
				# Replace multiple spaces with single
				val = super(RecordModel, self).data(item).toString().replace(QtCore.QRegExp('[ ]+'), ' ')
				return QtCore.QVariant(val)

			elif item.column() == enum.kRecordColumn_Txdate:
				# Reformat date to only display time if available
				if super(RecordModel, self).data(item).toDateTime().time().toString() == "00:00:00":
					return QtCore.QVariant(super(RecordModel, self).data(item).toDate())

		return super(RecordModel, self).data(item, role)

	def toggleChecked(self, indexes):
		checkedRecords = []
		unCheckedRecords = []

		for index in indexes:
			recordId = self.index(index.row(), enum.kRecordColumn_RecordId).data().toPyObject()
			if self.index(index.row(), enum.kRecordColumn_Checked).data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
				checkedRecords.append(recordId)
			else:
				unCheckedRecords.append(recordId)

		with db.transaction():
			if unCheckedRecords:
				query = QtSql.QSqlQuery()
				query.prepare("""
					UPDATE records
					   SET checked=1, checkdate=CURRENT_TIMESTAMP
					 WHERE recordid IN (?)
					""")
				query.addBindValue(unCheckedRecords)
				if not query.execBatch(QtSql.QSqlQuery.ValuesAsColumns):
					raise Exception(query.lastError().text())
	
			if checkedRecords:
				query = QtSql.QSqlQuery()
				query.prepare("""
					UPDATE records
					   SET checked=0, checkdate=NULL
					 WHERE recordid IN (?)
					""")
				query.addBindValue(checkedRecords)
				if not query.execBatch(QtSql.QSqlQuery.ValuesAsColumns):
					raise Exception(query.lastError().text())

		self.select()

		for index in indexes:
			checkedIndex = self.index(index.row(), enum.kRecordColumn_Checked)
			self.dataChanged.emit(checkedIndex, checkedIndex)

	@utils.showWaitCursorDecorator
	def setData(self, index, value, role=QtCore.Qt.EditRole):
		""" Save new checkstate role changes in database
		"""
		if role == QtCore.Qt.CheckStateRole and index.column() == enum.kRecordColumn_Checked:
			self.toggleChecked([index])
			return True

		return False

	def headerData (self, section, orientation, role=QtCore.Qt.DisplayRole):
		""" Set the header labels for the view
		"""
		if role == QtCore.Qt.DisplayRole:
			if section == enum.kRecordColumn_Checked:
				return "Check"
			elif section == enum.kRecordColumn_Tags:
				return "Tags"
			elif section == enum.kRecordColumn_Date:
				return "Date"
			elif section == enum.kRecordColumn_AccountTypeName:
				return "Account"
			elif section == enum.kRecordColumn_Description:
				return "Description"
			elif section == enum.kRecordColumn_Txdate:
				return "TX date"
			elif section == enum.kRecordColumn_Amount:
				return "Amount"

		return QtCore.QVariant()

class TagModel(QtSql.QSqlTableModel):
	tagsChanged = QtCore.pyqtSignal()
	selectionChanged = QtCore.pyqtSignal('PyQt_PyObject')

	def __init__(self, parent=None):
		super(TagModel, self).__init__(parent=parent)
		self.__selectedTagNames = set()

		self.setTable('tags')
		self.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
		super(TagModel, self).select()

	def setRecordFilter(self, recordIds):
		""" List of record ids to limit tag data to display
			If no record ids are given then we still need to set 
			"0" to ensure that no record ids are matched
		"""
		self.setFilter(','.join([str(rec) for rec in recordIds or [0]]))

	def clearSelection(self):
		for row in xrange(self.rowCount()):
			index = self.index(row, enum.kTagsColumn_TagName)
			self.setData(index, QtCore.QVariant(QtCore.Qt.Unchecked), QtCore.Qt.CheckStateRole)

	def setData(self, index, value, role=QtCore.Qt.EditRole):
		""" Handle checkstate role changes
		"""
		if index.column() == enum.kTagsColumn_TagName:
			if role == QtCore.Qt.CheckStateRole:
				tagName = index.data().toPyObject()
	
				if value.toPyObject() == QtCore.Qt.Checked:
					if tagName in self.__selectedTagNames:
						# Do nothing if tag has not changed
						return False
					self.__selectedTagNames.add(tagName)
				else:
					if tagName not in self.__selectedTagNames:
						# Do nothing if tag has not changed
						return False
					self.__selectedTagNames.remove(tagName)
	
				self.dataChanged.emit(index, index)
				self.selectionChanged.emit(self.__selectedTagNames)
				return True 
	
			elif role == QtCore.Qt.EditRole:
				# Save changes to tag name in database
				return super(TagModel, self).setData(index, value, role)

		return False

	def data(self, item, role=QtCore.Qt.DisplayRole):

		if role == QtCore.Qt.DisplayRole:

			if item.column() == enum.kTagsColumn_RecordIds:
				tags = set([int(i) for i in super(TagModel, self).data(item).toString().split(',') if i])
				return QtCore.QVariant(tags)

			elif item.column() in (enum.kTagsColumn_Amount_in, enum.kTagsColumn_Amount_out):
				amount = '%.2f' % super(TagModel, self).data(item).toPyObject()
				if amount == '0.00':
					return QtCore.QVariant()
				else:
					return QtCore.QVariant(amount)

		if  role == QtCore.Qt.CheckStateRole and item.column() == enum.kTagsColumn_TagName:
			if item.data().toPyObject() in self.__selectedTagNames:
				return QtCore.QVariant(QtCore.Qt.Checked)
			else:
				return QtCore.QVariant(QtCore.Qt.Unchecked)

		return super(TagModel, self).data(item, role)

	def flags(self, index):
		flags = super(TagModel, self).flags(index)

		if index.column() == enum.kTagsColumn_TagName:
			flags |= QtCore.Qt.ItemIsUserCheckable
		
		# Only allow tag name to be editable
		if index.column() != enum.kTagsColumn_TagName:
			flags ^= QtCore.Qt.ItemIsEditable

		return flags

	def selectStatement(self):
		if self.tableName().isEmpty():
			return QtCore.QString()

		queryFilter = self.filter()
		queryFilter = 'AND r.recordid IN (%s)' %  queryFilter if queryFilter else ''

		query = """
			   SELECT t.tagid, t.tagname,
			          ARRAY_TO_STRING(ARRAY_AGG(r.recordid), ',') AS recordids,
			          SUM(CASE WHEN r.amount > 0 THEN r.amount ELSE 0 END) AS amount_in,
			          ABS(SUM(CASE WHEN r.amount < 0 THEN r.amount ELSE 0 END)) AS amount_out
			          FROM tags t
			LEFT JOIN recordtags rt ON rt.tagid=t.tagid
			LEFT JOIN records r ON r.recordid=rt.recordid
			      %s
			    WHERE t.userid=%d
			 GROUP BY t.tagid
		""" % (queryFilter, db.userId)

		return query

	def headerData (self, section, orientation, role):
		if role == QtCore.Qt.DisplayRole:
			if section == enum.kTagsColumn_TagName:
				return "tag"
			elif section == enum.kTagsColumn_Amount_in:
				return "in"
			elif section == enum.kTagsColumn_Amount_out:
				return "out"
		return QtCore.QVariant()

	def addTag(self, tagName):
		query = QtSql.QSqlQuery()
		query.prepare("""
			INSERT INTO tags (tagname, userid)
			     VALUES (?, ?)
			  RETURNING tagid
		""")
		query.addBindValue(tagName)
		query.addBindValue(db.userId)

		if not query.exec_():
			raise Exception(query.lastError().text())
		
		query.next()
		insertId = query.value(0).toPyObject() 
		self.select()
		self.tagsChanged.emit()
		return insertId

	def removeTag(self, tagId):
		currentIndex = self.index(0, enum.kTagsColumn_TagId)
		match = self.match(currentIndex, QtCore.Qt.DisplayRole, tagId, 1, QtCore.Qt.MatchExactly)
		assert match
		match = match[0]

		# Ensure this tag is unchecked
		self.setData(self.index(match.row(), enum.kTagsColumn_TagName), QtCore.QVariant(QtCore.Qt.Unchecked), QtCore.Qt.CheckStateRole)

		# Now delete it
		self.removeRows(match.row(), 1, QtCore.QModelIndex())
		self.select()
		self.tagsChanged.emit()
	

	def addRecordTags(self, tagId, recordIds):
		if not recordIds:
			return False

		# Remove records that already have this tag
		currentIndex = self.index(0, enum.kTagsColumn_TagId)
		match = self.match(currentIndex, QtCore.Qt.DisplayRole, tagId, 1, QtCore.Qt.MatchExactly)
		if match:
			existingRecordsForTag = self.index(match[0].row(), enum.kTagsColumn_RecordIds).data().toPyObject()
			recordIds = set(recordIds) - existingRecordsForTag

		query = QtSql.QSqlQuery()
		query.prepare("""
			INSERT INTO recordtags (recordid, tagid)
			     VALUES (?, ?) 
		""")

		query.addBindValue(list(recordIds))
		query.addBindValue([tagId] * len(recordIds))

		if not query.execBatch():
			raise Exception(query.lastError().text())

		self.tagsChanged.emit()
		return self.select()
	

	def removeRecordTags(self, tagId, recordIds):

		if not recordIds:
			return False

		query = QtSql.QSqlQuery("""
			DELETE FROM recordtags
			      WHERE recordid in (%s)
			        AND tagid=%s
			""" % (','.join([str(i) for i in recordIds]), tagId))

		if query.lastError().isValid():
			raise Exception(query.lastError().text())

		self.tagsChanged.emit()
		return self.select()

class TagProxyModel(QtGui.QSortFilterProxyModel):
	# Signal emitted whenever there is a change to the filter
	filterChanged = QtCore.pyqtSignal()

	def __init__(self, parent=None):
		super(TagProxyModel, self).__init__(parent=parent)

	def lessThan(self, left, right):
		""" Define the comparison to ensure column data is sorted correctly
		"""
		if left.column() in (enum.kTagsColumn_Amount_in, enum.kTagsColumn_Amount_out):
			return left.data().toDouble()[0] > right.data().toDouble()[0]

		return super(TagProxyModel, self).lessThan(left, right)

class RecordProxyModel(QtGui.QSortFilterProxyModel):

	# Signal emitted whenever there is a change to the filter
	filterChanged = QtCore.pyqtSignal()

	def __init__(self, parent=None):
		super(RecordProxyModel, self).__init__(parent=parent)
		self.__reset()

	def __reset(self):
		""" Create or re-create all filter
		"""
		self._startDate = None
		self._endDate = None
		self._insertDate = None
		self._accountids = None
		self._hasTags = None
		self._checked = None
		self._creditFilter = None
		self._description = None
		self._amountFilter = None
		self._tagFilter = None
		self._amountOperator = None

	def clearFilters(self):
		""" Clears all filters - does *not* call invalidate
		"""
		self.__reset()

	def setInsertDate(self, insertDate):
		self._startDate = None
		self._endDate = None
		self._insertDate = insertDate
		self.invalidateFilter()

	def setStartDate(self, startDate):
		self._insertDate = None
		self._startDate = startDate
		self.invalidateFilter()

	def setEndDate(self, date):
		self._insertDate = None
		self._endDate = date
		self.invalidateFilter()

	def setAccountFilter(self, accountIds):
		if accountIds != self._accountids:
			self._accountids = accountIds
			self.invalidateFilter()
			
	def setHasTagsFilter(self, value):
		""" Set basic tag filter

			selection:
				None  - no filter
				True  - filter with tags
				False - filter with no tags
		"""
		if value != self._hasTags:
			self._hasTags = value
			self.invalidateFilter()

	def setTagFilter(self, tags):
		if tags != self._tagFilter:
			self._tagFilter = tags.copy()
			self.invalidateFilter()

	def setCheckedFilter(self, value):
		""" Checked records filter

			selection:
				None  - all
				True  - filter only checked
				False - filter not checked
		"""
		if value != self._checked:
			self._checked = value
			self.invalidateFilter()

	def setCreditFilter(self, value):
		""" Credit amount filter

			selection:
				None  - all
				True  - filter on credit
				False - filter on debit
		"""
		if value != self._creditFilter:
			self._creditFilter = value
			self.invalidateFilter()

	def setDescriptionFilter(self, text):
		""" Filter by description (case insensitive)
		"""
		if text != self._description:
			self._description = text
			self.invalidateFilter()

	def setAmountFilter(self, text, op=None):
		""" Set amount filter with optional operator
			If operator is None then a string comparison is done on amount start
		""" 
		if text != self._amountFilter or op != self._amountOperator:
			self._amountFilter = text
			self._amountOperator = op
			self.invalidateFilter()

	def invalidateFilter(self):
		""" Override invalidateFilter so that we can emit the filterChanged signal
		"""
		super(RecordProxyModel, self).invalidateFilter()
		self.sort(self.sortColumn(), self.sortOrder())
		self.filterChanged.emit()

	def filterAcceptsRow(self, sourceRow, parent):
		if self._startDate:
			if self.sourceModel().index(sourceRow, enum.kRecordColumn_Date, parent).data().toDate() < self._startDate:
				return False

		if self._endDate:
			if self.sourceModel().index(sourceRow, enum.kRecordColumn_Date, parent).data().toDate() > self._endDate:
				return False

		if self._insertDate:
			if self.sourceModel().index(sourceRow, enum.kRecordColumn_InsertDate, parent).data().toDateTime() != self._insertDate:
				return False

		if self._accountids:
			if self.sourceModel().index(sourceRow, enum.kRecordColumn_AccountTypeId).data().toPyObject() not in self._accountids:
				return False

		if self._hasTags is not None:
			hasTags = self.sourceModel().index(sourceRow, enum.kRecordColumn_Tags).data(QtCore.Qt.UserRole).toBool()
			if self._hasTags != hasTags:
				return False

		if self._checked is not None:
			isChecked = self.sourceModel().index(sourceRow, enum.kRecordColumn_Checked).data(QtCore.Qt.CheckStateRole).toPyObject() == QtCore.Qt.Checked
			if self._checked != isChecked:
				return False

		if self._creditFilter is not None:
			amount = self.sourceModel().index(sourceRow, enum.kRecordColumn_Amount).data(QtCore.Qt.UserRole).toPyObject()
			if self._creditFilter != (amount >= 0.0):
				return False

		if self._description:
			description = self.sourceModel().index(sourceRow, enum.kRecordColumn_Description).data().toString()
			if not description.contains(self._description, QtCore.Qt.CaseInsensitive):
				return False

		if self._amountFilter:
			amount = self.sourceModel().index(sourceRow, enum.kRecordColumn_Amount).data().toString()
			if self._amountOperator is None:
				# Filter as string matching start
				if not amount.startsWith(self._amountFilter):
					return False
			else:
				# Use operator to perform match
				if not self._amountOperator(float(amount), float(self._amountFilter)):
					return False
				
		if self._tagFilter:
			tags = self.sourceModel().index(sourceRow, enum.kRecordColumn_Tags).data(QtCore.Qt.UserRole).toString()
			if not set(self._tagFilter).intersection(set(tags.split(','))):
				return False

		return True

	def lessThan(self, left, right):
		""" Define the comparison to ensure column data is sorted correctly
		"""
		leftVal = None
		rightVal = None

		if left.column() == enum.kRecordColumn_Tags:
			leftVal = len(left.data(QtCore.Qt.UserRole).toString().split(',', QtCore.QString.SkipEmptyParts))
			rightVal = len(right.data(QtCore.Qt.UserRole).toString().split(',', QtCore.QString.SkipEmptyParts))

		elif left.column() == enum.kRecordColumn_Checked:
			leftVal = left.data(QtCore.Qt.CheckStateRole).toPyObject()
			rightVal = right.data(QtCore.Qt.CheckStateRole).toPyObject()

		elif left.column() == enum.kRecordColumn_Amount:
			leftVal,_ = left.data(QtCore.Qt.UserRole).toDouble()
			rightVal,_ = right.data(QtCore.Qt.UserRole).toDouble()

		elif left.column() == enum.kRecordColumn_Date:
			leftVal =  left.data().toDate()
			rightVal = right.data().toDate()

			if leftVal == rightVal:
				# Dates are the same - sort by recordId just to ensure the results are consistent
				leftVal = self.sourceModel().index(left.row(), enum.kRecordColumn_RecordId).data().toPyObject()
				rightVal = self.sourceModel().index(right.row(), enum.kRecordColumn_RecordId).data().toPyObject()

		if leftVal or rightVal:
			return leftVal > rightVal

		return super(RecordProxyModel, self).lessThan(left, right)

class AccountEditModel(QtSql.QSqlTableModel):
	def __init__(self, parent=None):
		super(AccountEditModel, self).__init__(parent=parent)

	def data(self, item, role=QtCore.Qt.DisplayRole):
		if not item.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.ForegroundRole and self.isDirty(item):
			return QtCore.QVariant(QtGui.QColor(255, 165, 0))

		return super(AccountEditModel, self).data(item, role)

	def setData(self, index, value, role=QtCore.Qt.EditRole):
		# Don't flag cell as changed when it hasn't
		if role == QtCore.Qt.EditRole and index.data(QtCore.Qt.DisplayRole) == value:
			return False

		return super(AccountEditModel, self).setData(index, value, role)

	def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):

		if role == QtCore.Qt.DisplayRole:
			if section == enum.kAccountTypeColumn_AccountName:
				return 'Account Name'
			elif section == enum.kAccountTypeColumn_DateField:
				return 'Date'
			elif section == enum.kAccountTypeColumn_DescriptionField:
				return 'Desc'
			elif section == enum.kAccountTypeColumn_CreditField:
				return 'Credit'
			elif section == enum.kAccountTypeColumn_DebitField:
				return 'Debit'
			elif section == enum.kAccountTypeColumn_CurrencySign:
				return 'Currency sign'
			elif section == enum.kAccountTypeColumn_DateFormat:
				return 'Date formats'

		return QtCore.QVariant()

class AccountsModel(QtSql.QSqlTableModel):
	""" Model for accounts which stores selection.
		Underlying model is QSqlTableModel
	"""
	def __init__(self, parent=None):
		super(AccountsModel, self).__init__(parent=parent)
		self._checkedItems = set()

	def flags(self, index):
		""" Enable checkable account names
		"""
		flags = super(AccountsModel, self).flags(index)

		if index.column() == enum.kAccountTypeColumn_AccountName:
			flags |= QtCore.Qt.ItemIsUserCheckable

		return flags

	def data(self, index, role):
		if not index.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.CheckStateRole:
			if index.column() == enum.kAccountTypeColumn_AccountName:
				accountName = self.index(index.row(), enum.kAccountTypeColumn_AccountName).data().toString()
				if accountName in self._checkedItems:
					return QtCore.QVariant(QtCore.Qt.Checked)
				else:
					return QtCore.QVariant(QtCore.Qt.Unchecked)

		return super(AccountsModel, self).data(index, role)

	def setData(self, index, value, role):
		""" Set check state and preserve account name for use in data()
		"""
		if role == QtCore.Qt.CheckStateRole:
			if index.column() == enum.kAccountTypeColumn_AccountName:
				accountName = self.index(index.row(), enum.kAccountTypeColumn_AccountName).data().toString()
				if value.toPyObject() == QtCore.Qt.Checked:
					self._checkedItems.add(accountName)
				else:
					self._checkedItems.remove(accountName)
	
				self.dataChanged.emit(index, index)
				return True

		return False
