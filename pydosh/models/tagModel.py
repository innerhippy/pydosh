import re
from PySide import QtCore, QtGui, QtSql

from pydosh import enum, currency
from pydosh.database import db
import pydosh.pydosh_rc

class TagModel(QtSql.QSqlTableModel):
	tagsChanged = QtCore.Signal()
	selectionChanged = QtCore.Signal(list)

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
			self.setData(index, QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

	def setData(self, index, value, role=QtCore.Qt.EditRole):
		""" Handle checkstate role changes
		"""
		if index.column() == enum.kTagsColumn_TagName:
			if role == QtCore.Qt.CheckStateRole:
				tagName = index.data()

				if value == QtCore.Qt.Checked:
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
				tags = set([int(i) for i in super(TagModel, self).data(item).split(',') if i])
				return tags

			elif item.column() in (enum.kTagsColumn_Amount_in, enum.kTagsColumn_Amount_out):
				amount = super(TagModel, self).data(item)
				return currency.formatCurrency(amount) if amount else None

		elif role == QtCore.Qt.CheckStateRole and item.column() == enum.kTagsColumn_TagName:
			if item.data() in self.__selectedTagNames:
				return QtCore.Qt.Checked
			else:
				return QtCore.Qt.Unchecked

		elif role == QtCore.Qt.UserRole and item.column() in (enum.kTagsColumn_Amount_in, enum.kTagsColumn_Amount_out):
			return super(TagModel, self).data(item)

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
		if not self.tableName():
			return None

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
		return None

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
		insertId = query.value(0)
		self.select()
		self.tagsChanged.emit()
		return insertId

	def removeTag(self, tagId):
		currentIndex = self.index(0, enum.kTagsColumn_TagId)
		match = self.match(currentIndex, QtCore.Qt.DisplayRole, tagId, 1, QtCore.Qt.MatchExactly)
		assert match
		match = match[0]

		# Ensure this tag is unchecked
		self.setData(self.index(match.row(), enum.kTagsColumn_TagName), QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

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
			existingRecordsForTag = self.index(match[0].row(), enum.kTagsColumn_RecordIds).data()
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
	def __init__(self, parent=None):
		super(TagProxyModel, self).__init__(parent=parent)

	def lessThan(self, left, right):
		""" Define the comparison to ensure column data is sorted correctly
		"""
		if left.column() in (enum.kTagsColumn_Amount_in, enum.kTagsColumn_Amount_out):
			return left.data(QtCore.Qt.UserRole) > right.data(QtCore.Qt.UserRole)

		return super(TagProxyModel, self).lessThan(left, right)

