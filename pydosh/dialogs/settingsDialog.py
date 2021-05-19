from PyQt5 import QtCore, QtSql, QtWidgets

from ..ui_settings import Ui_Settings
from .. import enums

from ..delegates import AccountDelegate
from ..models import AccountEditModel


class SettingsDialog(Ui_Settings, QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)

        self.saveButton.clicked.connect(self.saveSettings)
        self.revertButton.clicked.connect(self.cancelSettings)
        self.closeButton.clicked.connect(self.close)
        self.addButton.clicked.connect(self.addAccount)
        self.deleteButton.clicked.connect(self.deleteAccount)

        self.enableCommit(False)

        model = AccountEditModel(self)
        model.setTable('accounttypes')
        model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        model.select()

        self.view.setModel(model)
        self.view.setColumnHidden(enums.kAccountType__AccountTypeId, True)
        self.view.verticalHeader().hide()
        self.view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.view.sortByColumn(enums.kAccountType__AccountName, QtCore.Qt.AscendingOrder)
        self.view.resizeColumnsToContents()
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.setItemDelegate(AccountDelegate(self))

        model.dataChanged.connect(self.view.clearSelection)
        model.dataChanged.connect(self.__dataChanged)
        model.beforeInsert.connect(self.validateNewAccount)

        self.model = model

    def __dataChanged(self, left, right):
        self.enableCommit(True)

    def validateNewAccount(self, record):
        try:
            if not record.value(enums.kAccountType__AccountName):
                raise Exception('Account name cannot be empty')

            value = int(record.value(enums.kAccountType__DateField))
            if value < 0:
                raise Exception('Date field must be set (index of date field)')

            value = int(record.value(enums.kAccountType__CreditField))
            if value < 0:
                raise Exception('Credit field must be set (index of credit field)')

            value  = int(record.value(enums.kAccountType__DebitField))
            if value < 0:
                raise Exception('Debit field must be set (index of debit field)')

            value = int(record.value(enums.kAccountType__DescriptionField))
            if value < 0:
                raise Exception('Description field must be set (index of description field)')

            value = int(record.value(enums.kAccountType__CurrencySign))
            if value not in (1, -1):
                raise Exception('Currency sign value must be 1 or -1')

            if not record.value(enums.kAccountType__DateFormat):
                raise Exception('"Date format cannot be empty (eg "dd/MM/yyyy")')

        except Exception as err:
            QtWidgets.QMessageBox.critical(self, 'Account failed', str(err), QtWidgets.QMessageBox.Ok)
            # Trash the bad record
            record.clear()

    def saveSettings(self):

        if not self.model.submitAll() and self.model.lastError().isValid():
            # If we've cleared the record from validateNewAccount() then the database error
            # will be empty. No need to issue a second error message
            if self.model.lastError().databaseText():
                QtWidgets.QMessageBox.critical(self, 'Error saving data', self.model.lastError().text(), QtWidgets.QMessageBox.Ok)
            self.model.revertAll()

        self.enableCommit(False)

    def cancelSettings(self): 
        self.model.revertAll()
        self.enableCommit(False)

    def enableCommit(self, enable):
        self.saveButton.setEnabled(enable)
        self.revertButton.setEnabled(enable)

    def addAccount(self):
        rowCount = self.model.rowCount()
        self.model.insertRow(rowCount)

        for column in range(1, self.model.columnCount()):
            index = self.model.index(rowCount, column)
            self.model.setData(index, None, QtCore.Qt.EditRole)

        index = self.model.index(rowCount, enums.kAccountType__AccountName)
        self.view.setCurrentIndex(index)
        self.view.edit(index)

    def deleteAccount(self):
        for index in self.view.selectionModel().selectedRows():

            accountTypeId = self.model.index(index.row(), enums.kAccountType__AccountTypeId).data()

            query = QtSql.QSqlQuery('SELECT COUNT(*) FROM records WHERE accounttypeid=%s' % accountTypeId)
            query.next()

            recordCount = query.value(0)

            if recordCount:
                QtWidgets.QMessageBox.critical(self, 'Account Delete ', 
                    'Cannot delete account, %d records exist for this account' % recordCount)
                return

            if index.isValid():
                self.model.removeRows(index.row(), 1, QtCore.QModelIndex())

        self.view.clearSelection()
        self.enableCommit(True)
