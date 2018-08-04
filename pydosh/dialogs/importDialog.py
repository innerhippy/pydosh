from PyQt5 import QtCore, QtGui, QtSql, QtWidgets

from pydosh import enum, currency
from pydosh.ui_import import Ui_Import
from pydosh.database import db
from pydosh.models import ImportModel

class UserCancelledException(Exception):
    """Exception to indicate user has cancelled the current operation
    """


class ImportDialog(Ui_Import, QtWidgets.QDialog):
    def __init__(self, files, parent=None):
        super(ImportDialog, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.__dataSaved = False
        self.__importInProgress = False
        self.__cancelImport = False

        self.progressBar.setVisible(False)

        self.currencyComboBox.addItems(currency.currencyCodes())
        self.currencyComboBox.setCurrentIndex(
            self.currencyComboBox.findText(currency.defaultCurrencyCode())
        )

        query = QtSql.QSqlQuery("""
                SELECT a.id, a.name, at.*
                  FROM accounts a
            INNER JOIN accounttypes at
                    ON at.accounttypeid=a.accounttypeid
                   AND a.userid=%d
            """ % db.userId)

        rec = query.record()
        self.accountTypeComboBox.addItem('Raw')

        while query.next():
            accountId =  query.value(rec.indexOf('id'))
            name = query.value(rec.indexOf('name'))
            dateIdx = query.value(rec.indexOf('datefield'))
            descIdx = query.value(rec.indexOf('descriptionfield'))
            creditIdx = query.value(rec.indexOf('creditfield'))
            debitIdx = query.value(rec.indexOf('debitfield'))
            currencySign = query.value(rec.indexOf('currencysign'))
            dateFormat = query.value(rec.indexOf('dateFormat'))
            self.accountTypeComboBox.addItem(name, (
                accountId, (dateIdx, descIdx, creditIdx, debitIdx, currencySign, dateFormat,))
            )

        self.accountTypeComboBox.setCurrentIndex(-1)

        model = ImportModel(files)

        self.importCancelButton.setEnabled(False)
        self.selectAllButton.setEnabled(False)
        self.view.setModel(model)
        model.modelReset.connect(self.view.expandAll)
        self.view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.view.expandAll()

        selectionModel = self.view.selectionModel()
        selectionModel.selectionChanged.connect(self._recordsSelected)
        self.accountTypeComboBox.currentIndexChanged.connect(self._accountChanged)

        self.importCancelButton.clicked.connect(self.__importCancelPressed)
        self.selectAllButton.clicked.connect(self.view.selectAll)
        self.closeButton.clicked.connect(self.__close)

        self.accountTypeComboBox.setCurrentIndex(0)

    def _accountChanged(self, index):
        model = self.view.model()
        selection = self.accountTypeComboBox.itemData(index, QtCore.Qt.UserRole)

        # If not 'Raw' (ie index 0) then extract the account data
        if selection is not None:
            selection = selection[1]

        model.accountChanged(selection)
        self.selectAllButton.setEnabled(bool(model.numRecordsToImport()))
        self.__setCounters()

        for column in range(model.columnCount()):
            self.view.resizeColumnToContents(column)

    def __importCancelPressed(self):
        if self.__importInProgress:
            self.__cancelImport = True
        else:
            self.__importRecords()

    def __setCounters(self):
        model = self.view.model()
        self.errorsCounter.setNum(model.numBadRecords())
        self.importedCounter.setNum(model.numRecordsImported())
        self.toImportCounter.setNum(model.numRecordsToImport())

    def _recordsSelected(self):
        """ Enable button cancel when we have selection
        """
        numSelected = len(self.view.selectionModel().selectedRows())
        self.selectedCounter.setNum(numSelected)
        self.importCancelButton.setEnabled(bool(numSelected))

    def __close(self):
        """ Exit with bool value to indicate if data was saved,
            but not if it's our initial model
        """
        self.done(self.__dataSaved)

    def __importRecords(self):
        """ Import selected rows to database
        """

        if self.currencyComboBox.currentIndex() == -1:
            QtWidgets.QMessageBox.critical(
                self,
                'Import Error',
                'Please select currency',
                QtWidgets.QMessageBox.Ok
            )
            return

        currencyCode = self.currencyComboBox.currentText()
        accountId, _ = self.accountTypeComboBox.itemData(self.accountTypeComboBox.currentIndex(), QtCore.Qt.UserRole)

        model = self.view.model()
        selectionModel = self.view.selectionModel()
        indexes = selectionModel.selectedRows()

        if len(indexes) == 0:
            return

        try:
            self.progressBar.setVisible(True)

            self.progressBar.setValue(0)
            self.progressBar.setMaximum(len(indexes))
            self.view.clearSelection()

            self.__importInProgress = True
            self.closeButton.setEnabled(False)
            self.selectAllButton.setEnabled(False)
            self.importCancelButton.setText('Cancel')
            self.importCancelButton.setEnabled(True)

            # Wrap the import in a transaction
            with db.transaction():
                for num, index in enumerate(indexes, 1):
                    model.saveRecord(accountId, currencyCode, index)
                    self.view.scrollTo(index, QtWidgets.QAbstractItemView.EnsureVisible)
                    self.__setCounters()
                    QtCore.QCoreApplication.processEvents()
                    self.progressBar.setValue(self.progressBar.value() +1)

                    if self.__cancelImport:
                        raise UserCancelledException

                if num:
                    self.__dataSaved = True
                    if QtWidgets.QMessageBox.question(
                        self, 'Import', 'Imported %d records successfully' % num,
                        QtWidgets.QMessageBox.Save|QtWidgets.QMessageBox.Cancel) != QtWidgets.QMessageBox.Save:
                        # By raising here we will rollback the database transaction
                        raise UserCancelledException

        except UserCancelledException:
            self.__dataSaved = False
            model.reset()

        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, 'Import Error', str(exc), QtWidgets.QMessageBox.Ok)

        finally:
            self.__cancelImport = False
            self.__importInProgress = False
            self.closeButton.setEnabled(True)
            self.importCancelButton.setText('Import')
            self.progressBar.setVisible(False)
            self.__setCounters()

            canImport = bool(model.numRecordsToImport())
            self.importCancelButton.setEnabled(canImport)
            self.selectAllButton.setEnabled(canImport)
