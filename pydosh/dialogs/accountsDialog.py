from PySide import QtCore, QtGui, QtSql

from pydosh.ui_accounts import Ui_Accounts
from pydosh import enum
from pydosh.database import db

#from pydosh.delegates import AccountDelegate
#from pydosh.models import UserAccountModel
from pydosh.models import AccountShareModel

try:
	from signaltracer import SignalTracer
except ImportError:
	from mpc.pyqtUtils.utils import SignalTracer

import pdb

class AccountsDialog(Ui_Accounts, QtGui.QDialog):
	def __init__(self, parent=None):
		super(AccountsDialog, self).__init__(parent=parent)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)
		self.closeButton.clicked.connect(self.close)
		self.saveButton.clicked.connect(self.saveSettings)
		self.revertButton.clicked.connect(self.revertChanges)
#		self.addAccountButton.clicked.connect(self.addAccount)
#		self.removeAccountButton.clicked.connect(self.deleteAccount)

		# Account shares, filter is set in switchAccounts
#		model = QtSql.QSqlRelationalTableModel(self)
#		model.setTable('accountshare')
#		model.setRelation(enum.kAccountShare_UserId, QtSql.QSqlRelation('users', 'userid', 'username'))
#		model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
#		model.select()
#		self.accountShareModel = model

		self.tracer = SignalTracer()
		self.accountShareView.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
#		model = QtSql.QSqlTableModel(self)
#		model.setTable('users')
#		model.setFilter('userid != %s' % db.userId)
#		model.select()
		self.accountShareView.setModel(AccountShareModel(self))
		self.accountShareView.setModelColumn(enum.kUsers_UserName)

		# Account Types dropdown (read-only)
		model = QtSql.QSqlTableModel(self)
#		model.setQuery('SELECT accounttypeid, accountname FROM accounttypes')
		model.setTable('accounttypes')
		self.accountType.setModel(model)
		self.accountType.setModelColumn(enum.kAccountTypeColumn_AccountName)
		model.select()

		# Accounts model
		model = QtSql.QSqlRelationalTableModel(self)
		model.setTable('accounts')
		model.setFilter('userid=%s' % db.userId)
		model.setSort(enum.kAccounts_Name, QtCore.Qt.AscendingOrder)
		model.setRelation(
			enum.kAccounts_AccountTypeId,
			QtSql.QSqlRelation('accounttypes', 'accounttypeid', 'accountname')
		)
		model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
#		self.tracer.monitor(self.accountShareView.model(), self.accountShareView, self, model, self.accountCombo)

		self.accountCombo.currentIndexChanged.connect(self.switchAccount)
		self.accountCombo.setModel(model)
		self.accountCombo.setModelColumn(enum.kAccounts_Name)
		self.accountCombo.setEditable(True)

		self.accountCombo.editTextChanged.connect(self.accountNameChanged)
		self.sortCode.textChanged.connect(self.sortCodeChanged)
		self.accountNo.textChanged.connect(self.accountNoChanged)
		self.accountType.activated[int].connect(self.accountTypeChanged)
		model.select()

	def switchAccount(self, index):
		""" Account changed by user, populate all fields
		"""
		if index == -1:
			print '-1'
			return
		print 'switchAccount', index
#		pdb.set_trace()
		model = self.accountCombo.model()
		self.sortCode.setText(model.index(index, enum.kAccounts_SortCode).data())
		self.accountNo.setText(model.index(index, enum.kAccounts_AccountNo).data())
		realAccountName = model.index(index, enum.kAccounts_AccountTypeId).data()
		self.accountType.setCurrentIndex(self.accountType.findText(realAccountName))


		# Set the filter on accountshare table
#		pdb.set_trace()
		accountId = model.index(index, enum.kAccounts_Id).data()

#		self.dumpModel('start 1')
		if self.accountShareView.model().hasChangesPending():
			if QtGui.QMessageBox.question(
				self,
				'Save changes',
				'There are unsaved changes to this account, cancel changes and proceed?',
				QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
			) == QtGui.QMessageBox.No:
				return
		self.accountShareView.model().changedAccount(accountId)
#		self.dumpModel('start 2')

	def sortCodeChanged(self, text):
		""" Set the new sort code
		"""
		model = self.accountCombo.model()
		currentIndex = self.accountCombo.currentIndex()
		index = model.index(currentIndex, enum.kAccounts_SortCode)
		if index.data() != text:
			print 'sortCodeChanged'
			model.setData(index, text)

	def accountNoChanged(self, text):
		""" Set the new account no
		"""
		model = self.accountCombo.model()
		currentIndex = self.accountCombo.currentIndex()
		index = model.index(currentIndex, enum.kAccounts_AccountNo)
		if index.data() != text:
			model.setData(index, text)

	def accountNameChanged(self, text):
		""" Set the new account alias name
		"""
		model = self.accountCombo.model()
		currentIndex = self.accountCombo.currentIndex()
		index = model.index(currentIndex, enum.kAccounts_Name)
		if index.data() != text:
			model.setData(index, text)

	def accountTypeChanged(self, idx):
		""" Set a new account type on the account
		"""
		newAccountTypeId = self.accountType.model().index(idx, enum.kAccountTypeColumn_AccountTypeId).data()
		model = self.accountCombo.model()
		currentIndex = self.accountCombo.currentIndex()
		index = model.index(currentIndex, enum.kAccounts_AccountTypeId)
		if self.accountType.currentText() != index.data():
			model.setData(index, newAccountTypeId)

	def revertChanges(self):
		self.accountCombo.model().reset()
		self.accountCombo.model().select()
		self.accountShareView.model().reset()
		self.accountCombo.setCurrentIndex(0)

	def dumpModel(self, text):
		model = self.accountCombo.model()
		print '-' * 20, text, '-' * 20
		for row in xrange(model.rowCount()):
			for column in xrange(model.columnCount()):
				index = model.index(row, column)
				if model.isDirty(index):
					print '%s: %d %d %r' % (text, row, column, index.data())
		print '-' * 50

	def saveSettings(self):
		self.accountShareView.model().submitAll()
		index = self.accountCombo.currentIndex()
		self.accountCombo.model().submitAll()
		self.accountCombo.setCurrentIndex(index)

class Noddy:
	def __init__(self, parent=None):
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

	#	if not self.model.submitAll() and self.model.lastError().isValid():
	#		# If we've cleared the record from validateNewAccount() then the database error
	#		# will be empty. No need to issue a second error message
	#		if self.	model.lastError().databaseText():
	#			QtGui.QMessageBox.critical(self, 'Error saving data', self.model.lastError().text(), QtGui.QMessageBox.Ok)
	#		self.model.revertAll()

	#	self.enableCommit(False)

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
