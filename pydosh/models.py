from PyQt4 import QtCore, QtGui, QtSql
import math
import pdb
import enum
from database import db
import pydosh_rc

class RecordModel(QtSql.QSqlTableModel):
	def __init__(self, userId, parent=None):
		super(RecordModel, self).__init__(parent=parent)
		self.__userId = userId
		self.__parameters = {}

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
#		self.__tagDict = {}

		model = QtSql.QSqlTableModel(self)
		model.setTable('recordtags')
		model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
		model.select()
		self.__recordTagModel = model

		#self.__loadTags()

	def __contains__(self, tagName):
		for row in xrange(self.rowCount()):
			if tagName == self.index(row, enum.kTagsColumn_TagName).data().toString():
				return True
		return False

	def __loadTags(self):
		# Store all recordids for existing tags
		self.__tagDict = {}

		query = QtSql.QSqlQuery("""
			SELECT tags.tagid, recordtags.recordid 
			FROM tags 
			INNER JOIN recordtags 
				ON recordtags.tagid=tags.tagid 
				AND tags.userid=%d
			""" % db.userId)

		if query.lastError().isValid():
			QtGui.QMessageBox.critical(None, 'Tag Error', query.lastError().text(), QtGui.QMessageBox.Ok)
			return

		while query.next():
			tagId, ok = query.value(0).toInt()
			if not ok:
				continue

			recordId, ok = query.value(1).toInt()
			if not ok:
				continue

			recordIds = self.__tagDict.setdefault(tagId, [])
			recordIds.append(recordId)

	def flags(self, index):
		defaultFlags = super(TagModel, self).flags(index)

		if index.isValid():
			return defaultFlags | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsSelectable

		return defaultFlags

	def data(self, item, role=QtCore.Qt.DisplayRole):

		if not item.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.CheckStateRole and item.column() == enum.kTagsColumn_TagName:
			# Extract tagId for this tag
			tagId, ok = super(TagModel, self).data(self.index(item.row(), enum.kTagsColumn_TagId)).toInt()
			if ok:
				recordIdsForTag = set(self.__getRecordIdsForTag(tagId))
				print recordIdsForTag
				if self.__recordIds.issubset(recordIdsForTag):
					print 'checked'
					return QtCore.Qt.Checked
				elif self.__recordIds.intersection(recordIdsForTag):
					print 'partial'
					return QtCore.Qt.PartiallyChecked
				else:
					print 'unchecked'
					return QtCore.Qt.Unchecked
					
#				if tagId in self.__tagDict:
#					if set(self.__recordIds).issubset(set(self.__tagDict[tagId])):
#						# All our selected records have this tag
##						print 'returning checked'
#						print 'checked'
#						return QtCore.Qt.Checked
#					elif set(self.__recordIds).intersection(set(self.__tagDict[tagId])):
#						# Some of our records contain this tag
#						print 'partial'
#						return QtCore.Qt.PartiallyChecked
#				# None of our records contain this tag
#				print 'unchecked'
#				return QtCore.Qt.Unchecked

		return super(TagModel, self).data(item, role)

	def __getRecordIdsForTag(self, tagId):
		for row in xrange(self.__recordTagModel.rowCount()):
			recordId, ok = self.__recordTagModel.index(row, enum.kRecordTagsColumn_RecordId).data().toInt()
			if ok:
				yield recordId
		
	def setData(self, index, value, role=QtCore.Qt.EditRole):

		if not index.isValid():
			return QtCore.QVariant()
		
		if role == QtCore.Qt.CheckStateRole:

			tagId = self.index(index.row(), enum.kTagsColumn_TagId).data().toInt()[0]

			if value.toInt()[0] == QtCore.Qt.Unchecked:
				#print 'before', set(self.__getRecordIdsForTag(tagId)),
				self.__removeTagsFromRecords(tagId)
				#print 'after', set(self.__getRecordIdsForTag(tagId))
			else:
				self.__addTagsToRecords(tagId)

			self.dataChanged.emit(index, index)
			return True

		return super(TagModel, self).setData(index, value, role)
	
	def __removeTagsFromRecords(self, tagId):
		""" Delete a tag from our records
		"""
		for row in xrange(self.__recordTagModel.rowCount()):
			recordId, ok = self.__recordTagModel.index(row, enum.kRecordTagsColumn_RecordId).data().toInt()
			if not ok or recordId not in self.__recordIds:
				continue

			recordTagId, ok = self.__recordTagModel.index(row, enum.kRecordTagsColumn_TagId).data().toInt()
			if not ok or recordTagId != tagId:
				continue

			self.__recordTagModel.removeRows(row, 1)

		self.__recordTagModel.submitAll()

#		self.__tagDict.pop(tagId)


	def __addTagsToRecords(self, tagId):
		""" Assign the tag to our records
		"""
		#currentIds = self.__tagDict.setdefault(tagId, [])
		currentIds = set(self.__getRecordIdsForTag(tagId))
		print 'add currentIds', currentIds
		newRecordIds = self.__recordIds - currentIds
#		allRecordIds = list(set(self.__recordIds + currentIds))

		row = self.__recordTagModel.rowCount()
		self.__recordTagModel.insertRows(row, 1)

		for recordId in newRecordIds:
			# Only one row at a time can be inserted when using the OnFieldChange or OnRowChange update strategies.
			self.__recordTagModel.insertRows(row, 1)
			self.__recordTagModel.setData(self.__recordTagModel.index(row, enum.kRecordTagsColumn_RecordId), QtCore.QVariant(recordId))
			self.__recordTagModel.setData(self.__recordTagModel.index(row, enum.kRecordTagsColumn_TagId), QtCore.QVariant(tagId))

		self.__recordTagModel.submitAll()

#		self.__tagDict[tagId] = allRecordIds


	def addTag(self, tagName):
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
			elif section == enum.kAccountTypeColumn_TypeField:
				return 'Type'
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
