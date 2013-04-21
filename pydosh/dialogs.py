from PyQt4 import QtCore, QtGui, QtSql
from ui_settings import Ui_Settings
from ui_login import Ui_Login
from ui_import import Ui_Import
import enum
import utils
from database import db, DatabaseNotInitialisedException, ConnectionException
from delegates import AccountDelegate
from models import AccountModel, ImportModel

class UserCancelledException(Exception):
	""" Exception to indicate user has cancelled the current operation
	"""

class ImportDialog(Ui_Import, QtGui.QDialog):
	def __init__(self, records, accountId, parent=None):
		super(ImportDialog, self).__init__(parent=parent)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)
		self.__accountId = accountId
		self.__importInProgress = False
		self.__cancelImport = False

		self.progressBar.setVisible(False)
		model = ImportModel(records, self)
		db.commit.connect(model.save)
		db.rollback.connect(model.reset)

		self.importCancelButton.clicked.connect(self.__importCancelPressed)
		self.selectAllButton.clicked.connect(self.view.selectAll)

		proxy = QtGui.QSortFilterProxyModel(model)
		proxy.setSourceModel(model)
		proxy.setFilterKeyColumn(0)

		self.view.setModel(proxy)
		self.view.verticalHeader().hide()
		self.view.setSortingEnabled(True)
		self.view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.view.resizeColumnsToContents()
		self.view.horizontalHeader().setStretchLastSection(True)
		self.view.sortByColumn(2, QtCore.Qt.AscendingOrder)
		self.view.resizeColumnsToContents()

		self.closeButton.clicked.connect(self.__close)
		self.view.selectionModel().selectionChanged.connect(self.__recordsSelected)

		self.importCancelButton.setEnabled(False)
		
		self.selectAllButton.setEnabled(bool(model.numRecordsToImport()))

		self.__setCounters()

	def __importCancelPressed(self):
		if self.__importInProgress:
			self.__cancelImport = True
		else:
			self.__importRecords()

	def __setCounters(self):
		model = self.view.model().sourceModel()
		self.errorsCounter.setNum(model.numBadRecords())
		self.importedCounter.setNum(model.numRecordsImported())
		self.toImportCounter.setNum(model.numRecordsToImport())

	def __recordsSelected(self):
		""" Enable button cancel when we have selection
		"""
		numSelected = len(self.view.selectionModel().selectedRows())
		self.selectedCounter.setNum(numSelected)
		self.importCancelButton.setEnabled(bool(numSelected))

	def __close(self):
		self.done(self.view.model().sourceModel().dataSaved)

	def __importRecords(self):
		selectionModel = self.view.selectionModel()
		indexes = selectionModel.selectedRows()

		if len(indexes) == 0:
			return

		try:
			self.progressBar.setVisible(True)

			proxyModel = self.view.model()
			dataModel = proxyModel.sourceModel()
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
					dataModel.saveRecord(self.__accountId, proxyModel.mapToSource(index))
					self.view.scrollTo(index, QtGui.QAbstractItemView.EnsureVisible)
					self.view.resizeColumnsToContents()
					self.__setCounters()
					QtCore.QCoreApplication.processEvents()
					self.progressBar.setValue(self.progressBar.value() +1)
					
					if self.__cancelImport:
						raise UserCancelledException

				if num:
					if QtGui.QMessageBox.question(
						self, 'Import', 'Imported %d records successfully' % num,
						QtGui.QMessageBox.Save|QtGui.QMessageBox.Cancel) != QtGui.QMessageBox.Save:
						# By raising here we will rollback the database transaction
						raise UserCancelledException

		except UserCancelledException:
			dataModel.reset()

		except Exception, exc:
			QtGui.QMessageBox.critical(self, 'Import Error', str(exc), QtGui.QMessageBox.Ok)

		finally:
			self.__cancelImport = False
			self.__importInProgress = False
			self.closeButton.setEnabled(True)
			self.importCancelButton.setText('Import')
			self.progressBar.setVisible(False)

			canImport = bool(dataModel.numRecordsToImport())
			self.importCancelButton.setEnabled(canImport)
			self.selectAllButton.setEnabled(canImport)


class SettingsDialog(Ui_Settings, QtGui.QDialog):
	def __init__(self, userId, parent=None):
		super(SettingsDialog, self).__init__(parent=parent)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)

		self.saveButton.clicked.connect(self.saveSettings)
		self.revertButton.clicked.connect(self.cancelSettings)
		self.closeButton.clicked.connect(self.close)
		self.addButton.clicked.connect(self.addAccount)
		self.deleteButton.clicked.connect(self.deleteAccount)

		self.enableCommit(False)

		model = AccountModel(self)
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
			if record.value(enum.kAccountTypeColumn_AccountName).toString().isEmpty():
				raise Exception('Account name cannot be empty')

			value, ok = record.value(enum.kAccountTypeColumn_DateField).toInt()
			if not ok or value < 0:
				raise Exception('Date field must be set (index of date field)')

			value, ok = record.value(enum.kAccountTypeColumn_CreditField).toInt()
			if not ok or value < 0:
				raise Exception('Credit field must be set (index of credit field)')

			value, ok = record.value(enum.kAccountTypeColumn_DebitField).toInt()
			if not ok or value < 0:
				raise Exception('Debit field must be set (index of debit field)')

			if record.value(enum.kAccountTypeColumn_DescriptionField).toString().isEmpty():
				raise Exception('Description field must be set (index of description field)')

			value, ok = record.value(enum.kAccountTypeColumn_CurrencySign).toInt()
			if not ok or value not in (1, -1):
				raise Exception('Currency sign value must be 1 or -1')

			if record.value(enum.kAccountTypeColumn_DateFormat).toString().isEmpty():
				raise Exception('"Date format cannot be empty (eg "dd/MM/yyyy")')

		except Exception, err:
			QtGui.QMessageBox.critical(self, 'Account failed', str(err), QtGui.QMessageBox.Ok)
			# Trash the bad record
			record.clear()

	def saveSettings(self):

		if not self.model.submitAll() and self.model.lastError().isValid():
			# If we've cleared the record from validateNewAccount() then the database error
			# will be empty. No need to issue a second error message
			if self.m_model.lastError().databaseText():
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
			self.model.setData(index, QtCore.QVariant(), QtCore.Qt.EditRole)

		index = self.model.index(rowCount, enum.kAccountTypeColumn_AccountName)
		self.view.setCurrentIndex(index)
		self.view.edit(index)

	def deleteAccount(self):
		for index in self.view.selectionModel().selectedRows():
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
