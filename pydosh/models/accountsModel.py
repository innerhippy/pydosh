from PyQt5 import QtCore, QtGui, QtSql

from pydosh import enums


class AccountEditModel(QtSql.QSqlTableModel):
    def __init__(self, parent=None):
        super(AccountEditModel, self).__init__(parent=parent)

    def data(self, item, role=QtCore.Qt.DisplayRole):
        if not item.isValid():
            return None

        if role == QtCore.Qt.ForegroundRole and self.isDirty(item):
            return QtGui.QColor(255, 165, 0)

        return super(AccountEditModel, self).data(item, role)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        # Don't flag cell as changed when it hasn't
        if role == QtCore.Qt.EditRole and index.data(QtCore.Qt.DisplayRole) == value:
            return False

        return super(AccountEditModel, self).setData(index, value, role)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):

        if role == QtCore.Qt.DisplayRole:
            if section == enums.kAccountType__AccountName:
                return 'Account Name'
            elif section == enums.kAccountType__DateField:
                return 'Date'
            elif section == enums.kAccountType__DescriptionField:
                return 'Description'
            elif section == enums.kAccountType__CreditField:
                return 'Credit'
            elif section == enums.kAccountType__DebitField:
                return 'Debit'
            elif section == enums.kAccountType__CurrencySign:
                return 'Currency Sign'
            elif section == enums.kAccountType__DateFormat:
                return 'Date Format'

        return None

