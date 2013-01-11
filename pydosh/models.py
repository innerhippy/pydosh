from PyQt4 import QtCore, QtGui, QtSql
import enum

class SqlTableModel(QtSql.QSqlTableModel):
	def __init__(self, userId, parent=None):
		super(SqlTableModel, self).__init__(parent=parent)
		self.__userId = userId

	def select(self):
		status = super(SqlTableModel, self).select()
		while self.canFetchMore():
			self.fetchMore()

		return status

	def selectStatement(self):
		if self.tableName().isEmpty():
			return QtCore.QString()

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
			WHERE r.userid=%d
			%s
		""" % (self.__userId, self.filter())

		
#		if not self.filter().isEmpty():
#			query.append(QLatin1String(" WHERE ")).append(filter());

		query +=  'ORDER BY r.date, r.description'
		return query
			
	def data(self, item, role):

		if not item.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.CheckStateRole and item.column() == enum.kRecordColumn_Checked:
			if super(SqlTableModel, self).data(item).toBool():
				return QtCore.Qt.Checked
			else:
				return QtCore.Qt.Unchecked

		if role == QtCore.Qt.ToolTipRole:
			if item.column() == enum.kRecordColumn_Tags:
				if super(SqlTableModel, self).data(item).toInt() > 0:
					# return getTagList(QSqlTableModel::data(index(item.row(), kRecordColumn_RecordId)).toInt())
					return 'some tags'
			elif item.column() == enum.kRecordColumn_Checked:
				if super(SqlTableModel, self).data(self.index(item.row(), enum.kRecordColumn_Checked)).toBool():
					return "Checked: " + super(SqlTableModel, self).data(self.index(item.row(), enum.kRecordColumn_CheckDate)).toDateTime().toString("dd/MM/yy hh:mm")

			elif item.column() == enum.kRecordColumn_Date:
				return "Imported: " + super(SqlTableModel, self).data(self.index(item.row(), enum.kRecordColumn_InsertDate)).toDateTime().toString("dd/MM/yy hh:mm")
		"""

				case kRecordColumn_Description:
					return QSqlTableModel::data(item).toString();
	
				default:
					break;
			}
			return QVariant();
		}
	
		// Return the number of tags
		if (role == Qt::UserRole && item.column() == kRecordColumn_Tags) {
			return QSqlTableModel::data(item).toInt();
		}
	
		if (role == Qt::BackgroundColorRole) {
			if (record(item.row()).value(kRecordColumn_Amount).toDouble() > 0.0)
				return QColor("#b6ffac");
			else
				return QColor("#ffd3cf");
		}
	
		if (role == Qt::DecorationRole) {
			if (item.column() == kRecordColumn_Tags && QSqlTableModel::data(item).toInt() >0) {
				return QIcon(QString::fromUtf8(":/icons/tag_yellow.png"));
			}
		}
	
		if (role == Qt::DisplayRole) {
	
			switch (item.column()) {
				case kRecordColumn_Checked:
				case kRecordColumn_Tags:
					break;
	
				case kRecordColumn_Amount:
					// Display absolute currency values. credit/debit is indicated by background colour
					return QString::number(fabs(QSqlTableModel::data(item).toDouble()), 'f', 2);
	
				case kRecordColumn_Balance:
					return QString::number(QSqlTableModel::data(item).toDouble(), 'f', 2);
	
				case kRecordColumn_Description:
					// Truncate the description field to 30 chars
					return QSqlTableModel::data(item).toString().left(30);
	
				case kRecordColumn_Date:
					return QSqlTableModel::data(item).toDate();
	
				case kRecordColumn_AccountType:
				case kRecordColumn_Type:
					return QSqlTableModel::data(item);
	
				case kRecordColumn_Txdate:
					if (QSqlTableModel::data(item).toDateTime().time().toString() == "00:00:00")
						return QSqlTableModel::data(item).toDate();
					else 
						return QSqlTableModel::data(item).toDateTime();
	
				default:
					break;
			}
			return QVariant();
		}
		"""
		return super(SqlTableModel, self).data(item, role)

	def headerData (self, section, orientation, role):

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

	def lessThanXXXXXXX(self, left, right):
		"""
		leftData = self.sourceModel().data(left)
		rightData = sourceModel().data(right)

		if left.column() == 1:
			return self.sourceModel().date(left, QtCore.Qt.UserRole)
		elif leftColumn() == 2:
			return self.sourceModel().date(left, QtCore.Qt.UserRole)

	switch (left.column()) {
		case kRecordColumn_Tags:
			return sourceModel()->data(left, Qt::UserRole).toInt() < sourceModel()->data(right, Qt::UserR
ole).toInt();
		case kRecordColumn_Checked:
			return sourceModel()->data(left, Qt::CheckStateRole).toInt() < sourceModel()->data(right, Qt:
:CheckStateRole).toInt();
		case kRecordColumn_Amount:
		case kRecordColumn_Balance:
			return sourceModel()->data(left).toDouble() < sourceModel()->data(right).toDouble();
		default:
			break;
	}

	return QSortFilterProxyModel::lessThan(left, right);
class 
		"""

