from PyQt4 import QtCore, QtGui, QtSql
import math
import pydosh_rc
import pdb
import enum

class SqlTableModel(QtSql.QSqlTableModel):
	def __init__(self, userId, parent=None):
		super(SqlTableModel, self).__init__(parent=parent)
		self.__userId = userId
		self.__parameters = {}

	def select(self):
		status = super(SqlTableModel, self).select()
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
			if super(SqlTableModel, self).data(item).toBool():
				return QtCore.Qt.Checked
			else:
				return QtCore.Qt.Unchecked

		if role == QtCore.Qt.ToolTipRole:
			if item.column() == enum.kRecordColumn_Tags:
				val, ok = super(SqlTableModel, self).data(item).toInt()
				if ok and val > 0:
					# return getTagList(QSqlTableModel::data(index(item.row(), kRecordColumn_RecordId)).toInt())
					return 'some tags'
			elif item.column() == enum.kRecordColumn_Checked:
				if super(SqlTableModel, self).data(self.index(item.row(), enum.kRecordColumn_Checked)).toBool():
					return "Checked: " + super(SqlTableModel, self).data(
							self.index(item.row(), enum.kRecordColumn_CheckDate)).toDateTime().toString("dd/MM/yy hh:mm")

			elif item.column() == enum.kRecordColumn_Date:
				return "Imported: " + super(SqlTableModel, self).data(
							self.index(item.row(), enum.kRecordColumn_InsertDate)).toDateTime().toString("dd/MM/yy hh:mm")

			elif item.column() == enum.kRecordColumn_Description:
				return super(SqlTableModel, self).data(item).toString()

		if role == QtCore.Qt.UserRole and item.column() == enum.kRecordColumn_Tags:
			# Return the number of tags
			val, ok = super(SqlTableModel, self).data(item).toInt()
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
				val, ok = super(SqlTableModel, self).data(item).toInt()
				if ok and val > 0:
					return QtGui.QIcon(':/icons/tag_yellow.png')


		if role == QtCore.Qt.DisplayRole:
			if item.column() in (enum.kRecordColumn_Checked, enum.kRecordColumn_Tags):
				# Don't display anything for these fields
				return QtCore.QVariant()

			elif item.column() == enum.kRecordColumn_Amount:
				# Display absolute currency values. credit/debit is indicated by background colour
				val, ok = super(SqlTableModel, self).data(item).toDouble()
				if ok:
					return QtCore.QString.number(math.fabs(val), 'f', 2)

			elif item.column() == enum.kRecordColumn_Description:
				# Truncate the description field to 30 chars
				return super(SqlTableModel, self).data(item).toString().left(30)

			elif item.column() == enum.kRecordColumn_Date:
				return super(SqlTableModel, self).data(item).toDate()

			elif item.column() == enum.kRecordColumn_Txdate:
				if super(SqlTableModel, self).data(item).toDateTime().time().toString() == "00:00:00":
					return super(SqlTableModel, self).data(item).toDate()
				else:
					return super(SqlTableModel, self).data(item).toDateTime()

		return super(SqlTableModel, self).data(item, role)

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


class AccountTableModel(QtSql.QSqlTableModel):
	def __init__(self, parent=None):
		super(AccountSettingsModel, self).__init__(parent=parent)

	def data(self, item, role=QtCore.Qt.DisplayRole):

		if not item.isValid():
			return QtCore.QVariant()


		if role == QtCore.Qt.BackgroundColorRole and self.isDirty(item):
				return QtGui.QColor(255,156,126)

		return super(AccountTableModel, self).data(item, role)

	def setData(self, index, value, role):

		if not index.isValid():
			return QtCore.QVariant()

		# Don't flag cell as changed when it hasn't
		if role == QtCore.Qt.EditRole and self.data(index, role) == value:
				return False

		return super(AccountTableModel, self).setData(index, value, role)
		

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
