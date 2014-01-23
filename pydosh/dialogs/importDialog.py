from PySide import QtCore, QtGui, QtSql

from pydosh import enum, currency
from pydosh.ui_import import Ui_Import
from pydosh.database import db
from pydosh.models import ImportModel

class UserCancelledException(Exception):
	"""Exception to indicate user has cancelled the current operation
	"""


class ImportDialog(Ui_Import, QtGui.QDialog):
	def __init__(self, files, parent=None):
		super(ImportDialog, self).__init__(parent=parent)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)
		self.__dataSaved = False
		self.__importInProgress = False
		self.__cancelImport = False
		self.__accountIdMap = {}

		self.progressBar.setVisible(False)

		self.currencyComboBox.addItems(currency.currencyCodes())
		self.currencyComboBox.setCurrentIndex(
			self.currencyComboBox.findText(currency.defaultCurrencyCode())
		)

		model = QtSql.QSqlTableModel()
		model.setTable('accounttypes')
		model.select()

		self.accountTypeComboBox.addItem('Raw')

		for row in xrange(model.rowCount()):
			name = model.index(row, enum.kAccountTypeColumn_AccountName).data()
			dateIdx = model.index(row, enum.kAccountTypeColumn_DateField).data()
			descIdx = model.index(row, enum.kAccountTypeColumn_DescriptionField).data()
			creditIdx = model.index(row, enum.kAccountTypeColumn_CreditField).data()
			debitIdx = model.index(row, enum.kAccountTypeColumn_DebitField).data()
			currencySign = model.index(row, enum.kAccountTypeColumn_CurrencySign).data()
			dateFormat = model.index(row, enum.kAccountTypeColumn_DateFormat).data()
			self.accountTypeComboBox.addItem(name,
				(dateIdx, descIdx, creditIdx, debitIdx, currencySign, dateFormat,)
			)
			self.__accountIdMap[row +1] = model.index(row, enum.kAccountTypeColumn_AccountTypeId).data()

		self.accountTypeComboBox.setCurrentIndex(-1)

		model = ImportModel(files)

		self.importCancelButton.setEnabled(False)
		self.selectAllButton.setEnabled(False)
		self.view.setModel(model)
		model.modelReset.connect(self.view.expandAll)
		self.view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
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
		model.accountChanged(self.accountTypeComboBox.itemData(index))
		self.selectAllButton.setEnabled(bool(model.numRecordsToImport()))
		self.__setCounters()

		for column in xrange(model.columnCount()):
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
		accountId = self.__accountIdMap[self.accountTypeComboBox.currentIndex()]

		model = self.view.model()
		selectionModel = self.view.selectionModel()
		indexes = selectionModel.selectedRows()
		currencyCode = self.currencyComboBox.currentText()

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
					self.view.scrollTo(index, QtGui.QAbstractItemView.EnsureVisible)
					self.__setCounters()
					QtCore.QCoreApplication.processEvents()
					self.progressBar.setValue(self.progressBar.value() +1)

					if self.__cancelImport:
						raise UserCancelledException

				if num:
					self.__dataSaved = True
					if QtGui.QMessageBox.question(
						self, 'Import', 'Imported %d records successfully' % num,
						QtGui.QMessageBox.Save|QtGui.QMessageBox.Cancel) != QtGui.QMessageBox.Save:
						# By raising here we will rollback the database transaction
						raise UserCancelledException

		except UserCancelledException:
			self.__dataSaved = False
			model.reset()

		except Exception, exc:
			QtGui.QMessageBox.critical(self, 'Import Error', str(exc), QtGui.QMessageBox.Ok)

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
