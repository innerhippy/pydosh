import re
from PyQt5 import QtCore, QtGui, QtSql

from pydosh import enum, currency, utils
from pydosh.database import db


class RecordModel(QtSql.QSqlTableModel):
    """ QSqlTableModel to represent the records table
    """
    def __init__(self, parent=None):
        super(RecordModel, self).__init__(parent=parent)
        self._highlightText = None

    def select(self):
        """ Buffer the select statement for large datasets
        """
        status = super(RecordModel, self).select()
        while self.canFetchMore():
            self.fetchMore()

        return status

    def isWritable(self, index):
        """ True if the row from the index is owned
            by the current user
        """
        return self.index(index.row(), enum.kRecords_UserId).data() == db.userId

    def flags(self, index):
        """ Set the flags to allow checkable items
        """
        flags = super(RecordModel, self).flags(index)
        if index.column() == enum.kRecords_Checked and self.isWritable(index):
            return flags | QtCore.Qt.ItemIsUserCheckable
        return flags

    def selectStatement(self):
        """ Returns the select statement for the record table
        """
        if not self.tableName():
            return None

        query = """
        SELECT r.recordid,
               r.checked,
               array_to_string(array_agg(t.tagname ORDER BY t.tagname), ','),
               r.checkdate,
               r.date,
               r.accountid,
               a2.userid,
               a.name,
               r.description,
               r.amount,
               r.insertdate,
               r.rawdata,
               r.currency
          FROM records r
     LEFT JOIN accounts a
            ON a.id=r.accountid
     LEFT JOIN accountshare acs
            ON acs.accountid=r.accountid
     LEFT JOIN recordtags rt
            ON rt.recordid=r.recordid
     LEFT JOIN tags t
            ON rt.tagid=t.tagid
    INNER JOIN records r2
            ON r2.recordid=r.recordid
    INNER JOIN accounts a2
            ON a2.id=r2.accountid
         WHERE (a.userid = %(userid)s
            OR acs.userid = %(userid)s)
      GROUP BY r.recordid, a.name, a2.userid
      ORDER BY r.date, r.recordid
    """ % {'userid': db.userId}

        return query

    def deleteRecords(self, indexes):
        """ Delete rows manually - bulk deletion way quicker than using the model
        """
        recordIds = (
            self.index(index.row(), enum.kRecords_RecordId).data()
                for index in indexes if self.isWritable(index)
        )

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
        """ Highlight text in desciption field
        """
        self._highlightText = text
#        self.beginResetModel()
#        self.reset()
#        self.endResetModel()

    def data(self, item, role=QtCore.Qt.DisplayRole):
        """ Return data from the model, formatted for viewing
        """
        if not item.isValid():
            return None

        if role == QtCore.Qt.CheckStateRole:
            if item.column() == enum.kRecords_Checked:
                if super(RecordModel, self).data(item):
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked

        elif role == QtCore.Qt.FontRole:
            if item.column() == enum.kRecords_Description:
                if self._highlightText and self._highlightText.lower() in item.data(QtCore.Qt.DisplayRole).lower():
                    font = QtGui.QFont()
                    font.setBold(True)
                    return font

        elif role == QtCore.Qt.ToolTipRole:
            if item.column() == enum.kRecords_Tags:
                # Show tag names for this record
                return ', '.join(item.data(QtCore.Qt.UserRole))

            elif item.column() == enum.kRecords_Checked:
                if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
                    text = "Checked: " + super(RecordModel, self).data(
                        self.index(item.row(), enum.kRecords_CheckDate)).toString("dd/MM/yy hh:mm")
                    return text

            elif item.column() == enum.kRecords_Date:
                # Show when the record was imported
                text = "Imported: " + super(RecordModel, self).data(
                    self.index(item.row(), enum.kRecords_InsertDate)).toString("dd/MM/yy hh:mm")
                return text

            elif item.column() == enum.kRecords_Description:
                # Full, raw text
                return super(RecordModel, self).data(item, QtCore.Qt.DisplayRole)

        elif role == QtCore.Qt.UserRole:
            if item.column() == enum.kRecords_Tags:
                # Tags as comma separated string (from database)
                tags = super(RecordModel, self).data(item, QtCore.Qt.DisplayRole)
                return tags.split(',') if tags else []

            elif item.column() == enum.kRecords_Amount:
                # signed float
                return super(RecordModel, self).data(item, QtCore.Qt.DisplayRole)

            elif item.column() == enum.kRecords_Date:
                # QDate object
                return super(RecordModel, self).data(item, QtCore.Qt.DisplayRole)

        elif role == QtCore.Qt.ForegroundRole:
            if item.column() == enum.kRecords_Amount:
                # Indicate credit/debit with colour
                if item.data(QtCore.Qt.UserRole) > 0.0:
                    return QtGui.QColor(0, 255, 0)
                else:
                    return QtGui.QColor(255, 0, 0)

        elif role == QtCore.Qt.DecorationRole:
            if item.column() == enum.kRecords_Tags:
                # Show tag icon if we have any
                if item.data(QtCore.Qt.UserRole):
                    return QtGui.QIcon(':/icons/tag_yellow.png')

        elif role == QtCore.Qt.DisplayRole:
            if item.column() in (enum.kRecords_Checked, enum.kRecords_Tags):
                # Don't display anything for these fields
                return None

            elif item.column() == enum.kRecords_Amount:
                # Display absolute currency values. credit/debit is indicated by background colour
                code = self.index(item.row(), enum.kRecords_Currency).data()
                return currency.toCurrencyStr(abs(super(RecordModel, self).data(item)), code)

            elif item.column() == enum.kRecords_Description:
                # Replace multiple spaces with single
                return re.sub('[ ]+', ' ', super(RecordModel, self).data(item))

            elif item.column() == enum.kRecords_Date:
                # Ensure date display is day/month/year, or I'll get confused.
                # Use UserRole to return QDate object
                return super(RecordModel, self).data(item, role).toString('dd/MM/yyyy')

        return super(RecordModel, self).data(item, role)

    def toggleChecked(self, indexes):
        checkedRecords = []
        unCheckedRecords = []

        for index in indexes:
            recordId = self.index(index.row(), enum.kRecords_RecordId).data()
            if self.index(index.row(), enum.kRecords_Checked).data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
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
            checkedIndex = self.index(index.row(), enum.kRecords_Checked)
            self.dataChanged.emit(checkedIndex, checkedIndex)

    @utils.showWaitCursorDecorator
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """ Save new checkstate role changes in database
        """
        if role == QtCore.Qt.CheckStateRole and index.column() == enum.kRecords_Checked:
            self.toggleChecked([index])
            return True

        return False

    def headerData (self, section, orientation, role=QtCore.Qt.DisplayRole):
        """ Set the header labels for the view
        """
        if role == QtCore.Qt.DisplayRole:
            if section == enum.kRecords_Checked:
                return "Check"
            elif section == enum.kRecords_Tags:
                return "Tags"
            elif section == enum.kRecords_Date:
                return "Date"
            elif section == enum.kRecords_AccountTypeName:
                return "Account"
            elif section == enum.kRecords_Description:
                return "Description"
            elif section == enum.kRecords_Amount:
                return "Amount"


class RecordProxyModel(QtCore.QSortFilterProxyModel):
    """ Proxy model for records table. Allows for fast filtering without the expense
        of extra SQL queries
    """
    # pyqtSignal emitted whenever there is a change to the filter
    filterChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(RecordProxyModel, self).__init__(parent=parent)
        self.__reset()

    def reset(self):
        self.beginResetModel()
        self.__reset()
        self.endResetModel()

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
            self._tagFilter = tags[:]
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
            self._description = text.lower()
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
        """ Filters row to display
        """
        if self._startDate:
            if self.sourceModel().index(sourceRow, enum.kRecords_Date, parent).data(QtCore.Qt.UserRole) < self._startDate:
                return False

        if self._endDate:
            if self.sourceModel().index(sourceRow, enum.kRecords_Date, parent).data(QtCore.Qt.UserRole) > self._endDate:
                return False

        if self._insertDate:
            if self.sourceModel().index(sourceRow, enum.kRecords_InsertDate, parent).data() != self._insertDate:
                return False

        if self._accountids:
            if self.sourceModel().index(sourceRow, enum.kRecords_AccountId).data() not in self._accountids:
                return False

        if self._hasTags is not None:
            hasTags = bool(self.sourceModel().index(sourceRow, enum.kRecords_Tags).data(QtCore.Qt.UserRole))
            if self._hasTags != hasTags:
                return False

        if self._checked is not None:
            isChecked = self.sourceModel().index(sourceRow, enum.kRecords_Checked).data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked
            if self._checked != isChecked:
                return False

        if self._creditFilter is not None:
            amount = self.sourceModel().index(sourceRow, enum.kRecords_Amount).data(QtCore.Qt.UserRole)
            if self._creditFilter != (amount >= 0.0):
                return False

        if self._description:
            description = self.sourceModel().index(sourceRow, enum.kRecords_Description).data()
            try:
                if not re.search(self._description, description, re.IGNORECASE):
                  return False
            except Exception, exc:
                pass

        if self._amountFilter:
            amount = self.sourceModel().index(sourceRow, enum.kRecords_Amount).data(QtCore.Qt.UserRole)
            if self._amountOperator is None:
                if self._amountFilter not in '{:.2f}'.format(amount):
                    return False
            else:
                # Use operator to perform match
                if not self._amountOperator(abs(float(amount)), float(self._amountFilter)):
                    return False

        if self._tagFilter:
            tags = self.sourceModel().index(sourceRow, enum.kRecords_Tags).data(QtCore.Qt.UserRole)
            if not set(self._tagFilter).intersection(set(tags)):
                return False

        return True

    def lessThan(self, left, right):
        """ Define the comparison to ensure column data is sorted correctly
        """
        leftVal = None
        rightVal = None

        if left.column() == enum.kRecords_Tags:
            leftVal = len(left.data(QtCore.Qt.UserRole))
            rightVal = len(right.data(QtCore.Qt.UserRole))

        elif left.column() == enum.kRecords_Checked:
            leftVal = left.data(QtCore.Qt.CheckStateRole)
            rightVal = right.data(QtCore.Qt.CheckStateRole)

        elif left.column() == enum.kRecords_Amount:
            leftVal = left.data(QtCore.Qt.UserRole)
            rightVal = right.data(QtCore.Qt.UserRole)

        elif left.column() == enum.kRecords_Date:
            leftVal =  left.data(QtCore.Qt.UserRole)
            rightVal = right.data(QtCore.Qt.UserRole)

            if leftVal == rightVal:
                # Dates are the same - sort by recordId just to ensure the results are consistent
                leftVal = self.sourceModel().index(left.row(), enum.kRecords_RecordId).data(QtCore.Qt.UserRole)
                rightVal = self.sourceModel().index(right.row(), enum.kRecords_RecordId).data(QtCore.Qt.UserRole)

        if leftVal or rightVal:
            return leftVal > rightVal

        return super(RecordProxyModel, self).lessThan(left, right)
