from PySide import QtCore, QtGui, QtSql

from ui_settings import Ui_Settings
from ui_login import Ui_Login
from ui_import import Ui_Import
import enum
import utils
from database import db, DatabaseNotInitialisedException, ConnectionException
from delegates import AccountDelegate
from models import AccountEditModel, ImportModel

import pdb

class UserCancelledException(Exception):
	""" Exception to indicate user has cancelled the current operation
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

	#@QtCore.Slot(QtGui.QItemSelection, QtGui.QItemSelection)
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
					model.saveRecord(accountId, index)
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


class SettingsDialog(Ui_Settings, QtGui.QDialog):
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
		self.view.setColumnHidden(enum.kAccountTypeColumn_AccountTypeId, True)
		self.view.verticalHeader().hide()
		self.view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.view.sortByColumn(enum.kAccountTypeColumn_AccountName, QtCore.Qt.AscendingOrder)
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
			if not record.value(enum.kAccountTypeColumn_AccountName):
				raise Exception('Account name cannot be empty')

			value = record.value(enum.kAccountTypeColumn_DateField)
			if value < 0:
				raise Exception('Date field must be set (index of date field)')

			value = record.value(enum.kAccountTypeColumn_CreditField)
			if value < 0:
				raise Exception('Credit field must be set (index of credit field)')

			value  = record.value(enum.kAccountTypeColumn_DebitField)
			if value < 0:
				raise Exception('Debit field must be set (index of debit field)')

			value = record.value(enum.kAccountTypeColumn_DescriptionField)
			if value < 0:
				raise Exception('Description field must be set (index of description field)')

			value = record.value(enum.kAccountTypeColumn_CurrencySign)
			if value not in (1, -1):
				raise Exception('Currency sign value must be 1 or -1')

			if not record.value(enum.kAccountTypeColumn_DateFormat):
				raise Exception('"Date format cannot be empty (eg "dd/MM/yyyy")')

		except Exception, err:
			QtGui.QMessageBox.critical(self, 'Account failed', str(err), QtGui.QMessageBox.Ok)
			# Trash the bad record
			record.clear()

	def saveSettings(self):

		if not self.model.submitAll() and self.model.lastError().isValid():
			# If we've cleared the record from validateNewAccount() then the database error
			# will be empty. No need to issue a second error message
			if self.	model.lastError().databaseText():
				QtGui.QMessageBox.critical(self, 'Error saving data', self.model.lastError().text(), QtGui.QMessageBox.Ok)
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

		for column in xrange(1, self.model.columnCount()):
			index = self.model.index(rowCount, column)
			self.model.setData(index, None, QtCore.Qt.EditRole)

		index = self.model.index(rowCount, enum.kAccountTypeColumn_AccountName)
		self.view.setCurrentIndex(index)
		self.view.edit(index)

	def deleteAccount(self):
		for index in self.view.selectionModel().selectedRows():

			accountTypeId = self.model.index(index.row(), enum.kAccountTypeColumn_AccountTypeId).data()

			query = QtSql.QSqlQuery('SELECT COUNT(*) FROM records WHERE accounttypeid=%s' % accountTypeId)
			query.next()

			recordCount = query.value(0)

			if recordCount:
				QtGui.QMessageBox.critical(self, 'Account Delete ', 
					'Cannot delete account, %d records exist for this account' % recordCount)
				return

			if index.isValid():
				self.model.removeRows(index.row(), 1, QtCore.QModelIndex())

		self.view.clearSelection()
		self.enableCommit(True)


class LoginDialog(Ui_Login, QtGui.QDialog):
	def __init__(self, parent=None):
		super(LoginDialog, self).__init__(parent=parent)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)

		self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)

		self.connectionButton.clicked.connect(self.activateConnection)
		self.closeButton.clicked.connect(self.reject)

		self.hostnameEdit.setText(db.hostname)
		self.databaseEdit.setText(db.database)
		self.usernameEdit.setText(db.username)
		self.passwordEdit.setText(db.password)
		self.portSpinBox.setValue(db.port)

	def activateConnection(self):
		db.database = self.databaseEdit.text()
		db.hostname = self.hostnameEdit.text()
		db.username = self.usernameEdit.text()
		db.password = self.passwordEdit.text()
		db.port = self.portSpinBox.value()

		try:
			with utils.showWaitCursor():
				db.connect()
		except DatabaseNotInitialisedException:
			if QtGui.QMessageBox.question(
					self, 'Database', 
					'Database %s is empty, do you want to initialise it?' % db.database, 
					QtGui.QMessageBox.Yes|QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
				try:
					db.initialise()
				except ConnectionException, err:
					QtGui.QMessageBox.critical(self, 'Database ', str(err))
				else:
					QtGui.QMessageBox.information(self, 'Database', 'Database initialised successfully')
			else:
				return
		except ConnectionException, err:
			QtGui.QMessageBox.warning(self, 'Database', 'Failed to connect: %s' % str(err))
		else:
			self.accept()
