from PyQt5 import QtCore, QtSql

from pydosh import enum
from pydosh.database import db


class AccountShareModel(QtSql.QSqlTableModel):
    """ QSqlTable model to account share table
    """
    def __init__(self, parent=None):
        super(AccountShareModel, self).__init__(parent=parent)
        self.setTable('users')
        self.setFilter('userid != %s' % db.userId)
        self.setSort(enum.kUsers_UserName, QtCore.Qt.AscendingOrder)
        self.select()

        model = QtSql.QSqlRelationalTableModel(self)
        model.setTable('accountshare')
        model.setRelation(
            enum.kAccountShare_UserId,
            QtSql.QSqlRelation('users', 'userid', 'username')
        )
        model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        model.select()
        self.shareModel = model
        self.accountId = None

    def submitAll(self):
        status = self.shareModel.submitAll()
        if not status and self.shareModel.lastError().isValid():
            raise Exception(self.shareModel.lastError().text())
        return status

    def changedAccount(self, accountId):
        self.accountId = accountId
        self.shareModel.revertAll()
        self.shareModel.setFilter('accountshare.accountid=%s' % self.accountId)
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount()-1, self.columnCount()-1))

    def hasChangesPending(self):
        for row in xrange(self.shareModel.rowCount()):
            for column in xrange(self.shareModel.columnCount()):
                if self.shareModel.isDirty(self.shareModel.index(row, column)):
                    return True
        return False

    def flags(self, index):
        return QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled

    def data(self, item, role=QtCore.Qt.DisplayRole):
        if not item.isValid():
            return None

        if role == QtCore.Qt.CheckStateRole:
            sharedWith = [
                self.shareModel.index(row, enum.kAccountShare_UserId).data()
                    for row in xrange(self.shareModel.rowCount())
            ]
            if self.index(item.row(), enum.kUsers_UserName).data() in sharedWith:
                return QtCore.Qt.Checked
            else:
                return QtCore.Qt.Unchecked

        return super(AccountShareModel, self).data(item, role)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        """ Change the account share values
        """
        if role == QtCore.Qt.CheckStateRole:
            if value == QtCore.Qt.Unchecked:
                match = self.shareModel.match(
                    self.shareModel.index(0, enum.kAccountShare_UserId),
                    QtCore.Qt.DisplayRole,
                    index.data(QtCore.Qt.DisplayRole)
                )
                assert len(match) == 1, 'Expecting to find match in account shares'
                if not self.shareModel.removeRow(match[0].row()):
                    return False
            else:
                rowCount = self.shareModel.rowCount()
                userId = self.index(index.row(), enum.kUsers_UserId).data()
                self.shareModel.insertRow(rowCount)
                if not (
                    self.shareModel.setData(
                        self.shareModel.index(rowCount, enum.kAccountShare_AccountId), self.accountId)
                    and
                    self.shareModel.setData(
                        self.shareModel.index(rowCount, enum.kAccountShare_UserId), userId)
                    ):
                    return False

            self.dataChanged.emit(index, index)
            return True

        return False

