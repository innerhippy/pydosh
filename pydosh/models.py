from copy import deepcopy
import operator
from PyQt4 import QtCore, QtGui, QtSql
import enum
from database import db
import utils
import pydosh_rc

import pdb

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

class ImportModel(QtCore.QAbstractTableModel):
	def __init__(self, parent=None):
		super(ImportModel, self).__init__(parent=parent)
		self.__records = []
		self.__recordsRollback = None
		self.dataSaved = False
		self.__currentTimestamp = None

	def saveRecord(self, accountId, index):
		""" Saves the import record to the database
			Raises ImportException on error
		"""
		rec = self.__records[index.row()]

		# Ensure we record the same timestamp for this import
		self.__currentTimestamp = self.__currentTimestamp or QtCore.QDateTime.currentDateTime()

		query = QtSql.QSqlQuery()
		query.prepare("""
				INSERT INTO records
				(date, userid, accounttypeid, description, txdate, amount, insertdate, rawdata, checksum)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			""")

		query.addBindValue(rec.date)
		query.addBindValue(db.userId)
		query.addBindValue(accountId)
		query.addBindValue(rec.desc)
		query.addBindValue(rec.txdate)
		query.addBindValue(rec.credit or rec.debit)
		query.addBindValue(self.__currentTimestamp)
		query.addBindValue(QtCore.QString.fromUtf8(rec.data))
		query.addBindValue(rec.checksum)

		query.exec_()

		if query.lastError().isValid():
			raise ImportException(query.lastError().text())

		rec.imported = True
		self.dataSaved = True

		# Tell the view our data has changed
		self.dataChanged.emit(self.createIndex(index.row(), 0), self.createIndex(index.row(), self.columnCount() - 1))

	def reset(self):
		""" Slot to cancel all changes and revert to original records
		"""
		self.__records = deepcopy(self.__recordsRollback)
		self.dataSaved = False
		self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(self.rowCount() -1, self.columnCount() - 1))
		self.__currentTimestamp = None

	def save(self):
		""" Slot to persist changes to records
		"""
		self.__recordsRollback = deepcopy(self.__records)
		self.__currentTimestamp = None

	def flags(self, index):
		""" Only allow selection on records that can be imported
		"""
		flags = super(ImportModel, self).flags(index)

		if not self.__canImport(index):
			return flags ^ QtCore.Qt.ItemIsSelectable
		return flags


	def loadRecords(self, records):
		""" Import the records into our model
			An input record is a tuple containing
			(rawData, date, description, txDate, debit, credit, error,)

			The record is checked to see if it's already been imported into the database.
			For this we use the md5 checksum on the rawData field
		"""
		existingRecords = []
		query = QtSql.QSqlQuery('SELECT checksum from records where userid=%d' % db.userId)

		if query.lastError().isValid():
			raise ImportException(query.lastError().text())

		while query.next():
			existingRecords.append(query.value(0).toString())

		recordsLoaded = set()

		for record in set(records):
			rec = ImportRecord(*record)

			# Flag record as already imported
			if rec.valid and rec.checksum in existingRecords:
				rec.imported = True

			# Only import unique records or invalid ones (so we can see the error)
			if not rec.valid or rec.checksum not in recordsLoaded:
				recordsLoaded.add(rec.checksum)
				self.__records.append(rec)

		# Take a copy of the records in case we want to rollback
		self.save()

	def __canImport(self, index):
		""" Returns True if the record at index can be imported,
			ie no error and hasn't been imported yet
		"""
		rec = self.__records[index.row()]
		return not rec.imported and rec.valid

	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(self.__records)

	def numBadRecords(self):
		""" Returns the number of records with csv import errors
		"""
		return len([rec for rec in self.__records if not rec.valid])

	def numRecordsImported(self):
		""" Returns the number of records that have already been imported
		"""
		return len([rec for rec in self.__records if rec.imported])

	def numRecordsToImport(self):
		""" Returns the number of records left that can be imported
		"""
		return len([rec for rec in self.__records if rec.valid and not rec.imported])

	def data(self, item, role=QtCore.Qt.DisplayRole):

		if not item.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.ForegroundRole:
			if item.column() == 0:
				if not self.__records[item.row()].valid:
					return QtCore.QVariant(QtGui.QColor(255, 0, 0))
				elif self.__records[item.row()].imported:
					return QtCore.QVariant(QtGui.QColor(255, 165, 0))
				return QtCore.QVariant(QtGui.QColor(0, 255, 0))

		if role == QtCore.Qt.ToolTipRole:
			return QtCore.QVariant(QtCore.QString.fromUtf8(self.__records[item.row()].data))

		if role == QtCore.Qt.DisplayRole:
			if item.column() == enum.kImportColumn_Status:
				return QtCore.QVariant(self.__recordStatusToText(item))

			elif item.column() == enum.kImportColumn_Date:
				return QtCore.QVariant(self.__records[item.row()].date)

			elif item.column() == enum.kImportColumn_TxDate:
				return QtCore.QVariant(self.__records[item.row()].txdate)

			elif item.column() == enum.kImportColumn_Credit:
				amount =  self.__records[item.row()].credit
				return QtCore.QVariant('%.02f' % amount if amount else None)

			elif item.column() == enum.kImportColumn_Debit:
				amount =  self.__records[item.row()].debit
				return QtCore.QVariant('%.02f' % abs(amount) if amount else None)

			elif item.column() == enum.kImportColumn_Description:
				return QtCore.QVariant(self.__records[item.row()].desc)

		return QtCore.QVariant()

	def columnCount(self, index=QtCore.QModelIndex()):
		""" Needs to match headerData
		"""
		return 6

	def headerData (self, section, orientation, role):
		if role == QtCore.Qt.DisplayRole:
			if section == enum.kImportColumn_Status:
				return "Status"
			elif section == enum.kImportColumn_Date:
				return "Date"
			elif section == enum.kImportColumn_TxDate:
				return "TxDate"
			elif section == enum.kImportColumn_Credit:
				return "Credit"
			elif section == enum.kImportColumn_Debit:
				return "Debit"
			elif section == enum.kImportColumn_Description:
				return "Description"
		return QtCore.QVariant()

	def __recordStatusToText(self, index):
		""" Returns the record status:
			"imported" if imported, or the error text or None
		"""
		rec = self.__records[index.row()]

		if not rec.valid:
			return rec.error

		if rec.imported:
			return "Imported"

		return 'ready'

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
