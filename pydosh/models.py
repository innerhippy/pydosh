from PyQt4 import QtCore, QtGui, QtSql
import math
import pdb
import enum
from database import db
import pydosh_rc

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
		self.dataSaved = False

	def saveRecord(self, accountId, index):
		""" Saves the import record to the database
			Raises ImportException on error	
		"""
		rec = self.__records[index.row()]

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
		query.addBindValue(QtCore.QDateTime.currentDateTime())
		query.addBindValue(QtCore.QString.fromUtf8(rec.data))
		query.addBindValue(rec.checksum)

		query.exec_()

		if query.lastError().isValid():
			raise ImportException(query.lastError().text())

		rec.imported = True
		self.dataSaved = True

		# Tell the view our data has changed
		self.dataChanged.emit(self.createIndex(index.row(), 0), self.createIndex(index.row(), self.columnCount() - 1))

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

		for record in set(records):
			rec = ImportRecord(*record)
			if rec.checksum in existingRecords:
				rec.imported = True
			self.__records.append(rec)
	
	def canImport(self, index):
		""" Returns True if the record at index can be imported,
			ie no error and hasn't been imported yet
		"""
		rec = self.__records[index.row()]
		return not rec.imported and rec.valid

	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(self.__records)

	@property
	def numBadRecords(self):
		""" Returns the number of records with csv import errors
		"""
		return len([rec for rec in self.__records if not rec.valid])

	@property
	def numRecordsImported(self):
		""" Returns the number of records that have already been imported
		"""
		return len([rec for rec in self.__records if rec.imported])

	@property
	def numRecordsToImport(self):
		""" Returns the number of records left that can be imported
		"""
		return len([rec for rec in self.__records if rec.valid and not rec.imported])

	def data(self, item, role=QtCore.Qt.DisplayRole):

		if not item.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.BackgroundColorRole:
			if not self.__records[item.row()].valid:
				return QtGui.QColor("#ffd3cf")
			elif self.__records[item.row()].imported:
				return QtGui.QColor("#b6ffac")
			return QtCore.QVariant()

		if role == QtCore.Qt.ToolTipRole:
			if not self.__records[item.row()].valid:
				return self.__records[item.row()]
	
			return self.__records[item.row()].data 
	
		if role == QtCore.Qt.DisplayRole:
			if item.column() == 0:
				return self.__recordStatusToText(item)
			elif item.column() == 1:
				return self.__records[item.row()].date
			elif item.column() == 2:
				return self.__records[item.row()].txdate
			elif item.column() == 3:
				return self.__records[item.row()].desc
			elif item.column() == 4:
				return self.__records[item.row()].credit
			elif item.column() == 5:
				return self.__records[item.row()].debit

		return QtCore.QVariant()

	def columnCount(self, index=QtCore.QModelIndex()):
		""" Needs to match headerData
		"""
		return 6

	def headerData (self, section, orientation, role):
		if role == QtCore.Qt.DisplayRole:
			if section == 0:
				return "Status"
			elif section == 1:
				return "Date"
			elif section == 2:
				return "TxDate"
			elif section == 3:
				return "Description"
			elif section == 4:
				return "Credit"
			elif section == 5:
				return "Debit"
		return QtCore.QVariant()

	def __recordStatusToText(self, index):
		""" Returns the record status:
			"imported" if imported, or the error text or None
		"""
		rec = self.__records[index.row()]

		if not rec.valid:
			return rec.error
		elif rec.imported:
			return "Imported"
		else:
			return 'ready'

class RecordModel(QtSql.QSqlTableModel):
	def __init__(self, userId, parent=None):
		super(RecordModel, self).__init__(parent=parent)
		self.__userId = userId

	def select(self):
		status = super(RecordModel, self).select()
		while self.canFetchMore():
			self.fetchMore()

		return status

	def selectStatement(self):
		if self.tableName().isEmpty():
			return QtCore.QString()

		queryFilter = self.filter()
		queryFilter = 'AND ' + queryFilter if queryFilter else ''

		query = """
			SELECT 
				r.recordid, 
				r.checked,
				(select count(*) from recordtags rt where rt.recordid=r.recordid), 
				r.checkdate, 
				r.date, 
				users.username, 
				accounttypes.accountname, 
				r.description, 
				r.txdate, 
				r.amount, 
				r.insertdate, 
				r.rawdata 
			FROM records r
			INNER JOIN accounttypes ON accounttypes.accounttypeid=r.accounttypeid 
			INNER JOIN users ON users.userid=r.userid
			WHERE r.userid=%(userid)s
			%(filter)s
			ORDER BY r.date, r.description
		""" % {'userid': self.__userId, 'filter': queryFilter}

		return query

	def data(self, item, role=QtCore.Qt.DisplayRole):
		""" Return data from the model, formatted for viewing
		"""
		if not item.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.CheckStateRole and item.column() == enum.kRecordColumn_Checked:
			if super(RecordModel, self).data(item).toBool():
				return QtCore.Qt.Checked
			else:
				return QtCore.Qt.Unchecked

		if role == QtCore.Qt.ToolTipRole:
			if item.column() == enum.kRecordColumn_Tags:
				val, ok = super(RecordModel, self).data(item).toInt()
				if ok and val > 0:
					# return getTagList(QSqlTableModel::data(index(item.row(), kRecordColumn_RecordId)).toInt())
					return 'some tags'
			elif item.column() == enum.kRecordColumn_Checked:
				if super(RecordModel, self).data(self.index(item.row(), enum.kRecordColumn_Checked)).toBool():
					return "Checked: " + super(RecordModel, self).data(
							self.index(item.row(), enum.kRecordColumn_CheckDate)).toDateTime().toString("dd/MM/yy hh:mm")

			elif item.column() == enum.kRecordColumn_Date:
				return "Imported: " + super(RecordModel, self).data(
							self.index(item.row(), enum.kRecordColumn_InsertDate)).toDateTime().toString("dd/MM/yy hh:mm")

			elif item.column() == enum.kRecordColumn_Description:
				return super(RecordModel, self).data(item).toString()

		if role == QtCore.Qt.UserRole and item.column() == enum.kRecordColumn_Tags:
			# Return the number of tags
			val, ok = super(RecordModel, self).data(item).toInt()
			if ok:
				return val

		if role == QtCore.Qt.BackgroundColorRole:
			# Indicate credit/debit with row colour
			val, ok = self.record(item.row()).value(enum.kRecordColumn_Amount).toDouble()
			if ok:
				return QtGui.QColor("#b6ffac") if val > 0.0 else QtGui.QColor("#ffd3cf")

		if role == QtCore.Qt.DecorationRole:
			if item.column() == enum.kRecordColumn_Tags:
				# Show tag icon if we have any
				val, ok = super(RecordModel, self).data(item).toInt()
				if ok and val > 0:
					return QtGui.QIcon(':/icons/tag_yellow.png')


		if role == QtCore.Qt.DisplayRole:
			if item.column() in (enum.kRecordColumn_Checked, enum.kRecordColumn_Tags):
				# Don't display anything for these fields
				return QtCore.QVariant()

			elif item.column() == enum.kRecordColumn_Amount:
				# Display absolute currency values. credit/debit is indicated by background colour
				val, ok = super(RecordModel, self).data(item).toDouble()
				if ok:
					return QtCore.QString.number(math.fabs(val), 'f', 2)

			elif item.column() == enum.kRecordColumn_Description:
				# Truncate the description field to 30 chars
				return super(RecordModel, self).data(item).toString().left(30)

			elif item.column() == enum.kRecordColumn_Date:
				return super(RecordModel, self).data(item).toDate()

			elif item.column() == enum.kRecordColumn_Txdate:
				if super(RecordModel, self).data(item).toDateTime().time().toString() == "00:00:00":
					return super(RecordModel, self).data(item).toDate()
				else:
					return super(RecordModel, self).data(item).toDateTime()

		return super(RecordModel, self).data(item, role)

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
			elif section == enum.kRecordColumn_AccountType:
				return "Account"
			elif section == enum.kRecordColumn_Description:
				return "Description"
			elif section == enum.kRecordColumn_Txdate:
				return "TX date"
			elif section == enum.kRecordColumn_Amount:
				return "Amount"

		return QtCore.QVariant()

class TagModel(QtSql.QSqlTableModel):
	def __init__(self, recordIds, parent=None):
		super(TagModel, self).__init__(parent=parent)
		self.__recordIds = set(recordIds)
		model = QtSql.QSqlTableModel(self)
		model.setTable('recordtags')
		model.select()
		self.__recordTagModel = model

	def __contains__(self, tagName):
		""" Allows convenient:
				if "someTag" in model:
		"""
		for row in xrange(self.rowCount()):
			if tagName == self.index(row, enum.kTagsColumn_TagName).data().toString():
				return True
		return False

	def flags(self, index):
		return super(TagModel, self).flags(index) | QtCore.Qt.ItemIsUserCheckable

	def data(self, item, role=QtCore.Qt.DisplayRole):
		""" Tristate checkState:
				checked - all records have the tag
				partial - some records have the tag
				unchecked - no records have the tag
		"""
		if not item.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.CheckStateRole and item.column() == enum.kTagsColumn_TagName:
			# Extract tagId for this tag
			tagId, ok = super(TagModel, self).data(self.index(item.row(), enum.kTagsColumn_TagId)).toInt()
			if ok:
				recordIdsForTag = set(self.__getRecordIdsForTag(tagId))
				if self.__recordIds.issubset(recordIdsForTag):
					return QtCore.Qt.Checked
				elif self.__recordIds.intersection(recordIdsForTag):
					return QtCore.Qt.PartiallyChecked
				else:
					return QtCore.Qt.Unchecked

		return super(TagModel, self).data(item, role)

	def __getRecordIdsForTag(self, tagId):
		""" Generator to get all recordIds assigned to a given tag (id)
		"""
		for row in xrange(self.__recordTagModel.rowCount()):
			recordId, ok = self.__recordTagModel.index(row, enum.kRecordTagsColumn_RecordId).data().toInt()
			recordTagId, ok = self.__recordTagModel.index(row, enum.kRecordTagsColumn_TagId).data().toInt()

			if ok and tagId == recordTagId:
				yield recordId
		
	def setData(self, index, value, role=QtCore.Qt.EditRole):
		""" Handle checkstate role changes 
		"""
		if not index.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.CheckStateRole:

			tagId = self.index(index.row(), enum.kTagsColumn_TagId).data().toInt()[0]

			if value.toInt()[0] == QtCore.Qt.Unchecked:
				self.__removeTagsFromRecords(tagId)
			else:
				self.__addTagsToRecords(tagId)

			self.dataChanged.emit(index, index)
			return True

		return super(TagModel, self).setData(index, value, role)
	
	def __removeTagsFromRecords(self, tagId):
		""" Delete a tag from our records
		"""
		for row in reversed(xrange(self.__recordTagModel.rowCount())):
			recordId, ok = self.__recordTagModel.index(row, enum.kRecordTagsColumn_RecordId).data().toInt()
			if not ok or recordId not in self.__recordIds:
				continue

			recordTagId, ok = self.__recordTagModel.index(row, enum.kRecordTagsColumn_TagId).data().toInt()
			if not ok or recordTagId != tagId:
				continue

			self.__recordTagModel.removeRows(row, 1)
			self.__recordTagModel.submit()


	def __addTagsToRecords(self, tagId):
		""" Assign the tag to our records
		"""
		currentIds = set(self.__getRecordIdsForTag(tagId))
		newRecordIds = self.__recordIds - currentIds

		row = self.__recordTagModel.rowCount()
		self.__recordTagModel.insertRows(row, 1)

		for recordId in newRecordIds:
			# Only one row at a time can be inserted when using the OnFieldChange or OnRowChange update strategies.
			self.__recordTagModel.insertRows(row, 1)
			self.__recordTagModel.setData(self.__recordTagModel.index(row, enum.kRecordTagsColumn_RecordId), QtCore.QVariant(recordId))
			self.__recordTagModel.setData(self.__recordTagModel.index(row, enum.kRecordTagsColumn_TagId), QtCore.QVariant(tagId))

			self.__recordTagModel.submit()


	def addTag(self, tagName):
		""" Add a new tag and assign to our current records
		"""
		rowCount = self.rowCount()
		self.insertRows(rowCount, 1)
		self.setData(self.index(rowCount, enum.kTagsColumn_TagName), QtCore.QVariant(tagName))
		self.setData(self.index(rowCount, enum.kTagsColumn_UserId), QtCore.QVariant(db.userId))
		self.submit()

		tagId, ok = self.data(self.index(rowCount, enum.kTagsColumn_TagId)).toInt()
		if ok:
			self.__addTagsToRecords(tagId)


class SortProxyModel(QtGui.QSortFilterProxyModel):
	def __init__(self, parent=None):
		super(SortProxyModel, self).__init__(parent=parent)

	def lessThan(self, left, right):
		""" Define the comparison to ensure column data is sorted correctly
		"""
		leftData = self.sourceModel().data(left)
		rightData = self.sourceModel().data(right)

		if left.column() == enum.kRecordColumn_Tags:
			return self.sourceModel().data(left, QtCore.Qt.UserRole) < self.sourceModel().data(right, QtCore.Qt.UserRole)

		elif left.column() == enum.kRecordColumn_Checked:
			return self.sourceModel().data(left, QtCore.Qt.CheckStateRole) < self.sourceModel().data(right, QtCore.Qt.CheckStateRole)

		elif left.column() == enum.kRecordColumn_Amount:
			leftVal, leftOk = self.sourceModel().data(left).toDouble()
			rightVal, rightOk = self.sourceModel().data(right).toDouble()
			if leftOk and rightOk:
				return leftVal < rightVal

		return super(SortProxyModel, self).lessThan(left, right)


class AccountModel(QtSql.QSqlTableModel):
	def __init__(self, parent=None):
		super(AccountModel, self).__init__(parent=parent)

	def data(self, item, role=QtCore.Qt.DisplayRole):

		if not item.isValid():
			return QtCore.QVariant()


		if role == QtCore.Qt.BackgroundColorRole and self.isDirty(item):
				return QtGui.QColor(255,156,126)

		return super(AccountModel, self).data(item, role)

	def setData(self, index, value, role=QtCore.Qt.EditRole):

		if not index.isValid():
			return QtCore.QVariant()

		# Don't flag cell as changed when it hasn't
		if role == QtCore.Qt.EditRole and self.data(index, role) == value:
			return False

		return super(AccountModel, self).setData(index, value, role)

	def headerData (self, section, orientation, role=QtCore.Qt.DisplayRole):

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
