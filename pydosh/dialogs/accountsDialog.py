from PySide import QtCore, QtGui, QtSql

from pydosh.ui_accounts import Ui_Accounts
from pydosh import enum, utils
from pydosh.database import db
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
		self.saveButton.setEnabled(False)
		self.revertButton.setEnabled(False)
		self._changedMade = False
		self._allowAccountShareEdit = True
		self.addAccountButton.clicked.connect(self.addNewAccount)
		self.removeAccountButton.clicked.connect(self.removeAccount)

		# Account shares, filter is set in switchAccounts
		self.accountShareView.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
		model = AccountShareModel(self)
		self.accountShareView.setModel(model)
		model.dataChanged.connect(self.setButtonsEnabled)
		self.accountShareView.setModelColumn(enum.kUsers_UserName)

		# Account Types dropdown (read-only)
		model = QtSql.QSqlTableModel(self)
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

		self.tracer = SignalTracer()
#		self.tracer.monitor(self.accountShareView.model(), self.accountShareView, self, model, self.accountCombo)
		self.tracer.monitor(self.accountShareView.model(), model, self.accountCombo)

		self.accountCombo.currentIndexChanged.connect(self.switchAccount)
		self.accountCombo.setModel(model)
		self.accountCombo.setModelColumn(enum.kAccounts_Name)
		self.accountCombo.setEditable(True)

		self.accountCombo.editTextChanged.connect(self.accountNameChanged)
		self.sortCode.textChanged.connect(self.sortCodeChanged)
		self.accountNo.textChanged.connect(self.accountNoChanged)
		self.accountType.activated[int].connect(self.accountTypeChanged)
		model.select()

		self.accountCombo.setCurrentIndex(0)

	def addNewAccount(self):
		""" Add new account
			Disable account share until save has been committed
		"""
		model = self.accountCombo.model()
		row = model.rowCount()
		model.insertRow(row)
		index = model.index(row, enum.kAccounts_UserId)
		model.setData(index, db.userId)
		self.accountCombo.setCurrentIndex(row)

		# Disable edits to account share until we've commited. We need the ID's...
		self._allowAccountShareEdit = False
		self.setButtonsEnabled()

		# Set focus on the account name
		self.accountCombo.setFocus(QtCore.Qt.OtherFocusReason)

	def removeAccount(self):
		""" Delete an account.
			This will fail if account is referenced by records table
		"""
		index = self.accountCombo.currentIndex()
		self.accountCombo.removeItem(index)
		self.setButtonsEnabled()

	def switchAccount(self, index):
		""" Account changed by user, populate all fields
		"""
		if index == -1:
			return

		model = self.accountCombo.model()
		self.sortCode.setText(model.index(index, enum.kAccounts_SortCode).data())
		self.accountNo.setText(model.index(index, enum.kAccounts_AccountNo).data())
		realAccountName = model.index(index, enum.kAccounts_AccountTypeId).data()
		self.accountType.setCurrentIndex(self.accountType.findText(realAccountName))

		# Set the filter on accountshare table
		accountId = model.index(index, enum.kAccounts_Id).data()
		self.accountShareView.model().changedAccount(accountId)
		self._allowAccountShareEdit = True
		self.setButtonsEnabled()

	def setButtonsEnabled(self):
		""" Enable or disable save and revert buttons
			according to changes made to the model
		"""
		changesPending = False
		model = self.accountCombo.model()
		for row in xrange(model.rowCount()):
			for column in xrange(model.columnCount()):
				if model.isDirty(model.index(row, column)):
					changesPending = True
					break

		changesPending = changesPending or self.accountShareView.model().hasChangesPending()
		self.revertButton.setEnabled(changesPending)

		if changesPending:
			# Validate fields that have changed
			changesPending = (
				len(self.accountCombo.currentText().strip()) > 0
				and self.accountType.currentIndex() != -1
			)

		self.saveButton.setEnabled(changesPending)
		self.accountShareView.setEnabled(self._allowAccountShareEdit)

	def sortCodeChanged(self, text):
		""" Set the new sort code
		"""
		model = self.accountCombo.model()
		currentIndex = self.accountCombo.currentIndex()
		index = model.index(currentIndex, enum.kAccounts_SortCode)
		if index.data() != text:
			print 'sortCodeChanged'
			model.setData(index, text.strip())
		self.setButtonsEnabled()

	def accountNoChanged(self, text):
		""" Set the new account no
		"""
		model = self.accountCombo.model()
		currentIndex = self.accountCombo.currentIndex()
		index = model.index(currentIndex, enum.kAccounts_AccountNo)
		if index.data() != text:
			model.setData(index, text.strip())
		self.setButtonsEnabled()

	def accountNameChanged(self, text):
		""" Set the new account alias name
		"""
		model = self.accountCombo.model()
		currentIndex = self.accountCombo.currentIndex()
		index = model.index(currentIndex, enum.kAccounts_Name)
		if index.data() != text:
			model.setData(index, text.strip())
		self.setButtonsEnabled()

	def accountTypeChanged(self, idx):
		""" Set a new account type on the account
		"""
		newAccountTypeId = self.accountType.model().index(
			idx, enum.kAccountTypeColumn_AccountTypeId).data()
		model = self.accountCombo.model()
		currentIndex = self.accountCombo.currentIndex()
		index = model.index(currentIndex, enum.kAccounts_AccountTypeId)
		if self.accountType.currentText() != index.data():
			model.setData(index, newAccountTypeId)
		self.setButtonsEnabled()

	@utils.showWaitCursorDecorator
	def revertChanges(self):
		self.accountCombo.model().reset()
		self.accountCombo.model().select()
		self.accountShareView.model().reset()
		self._allowAccountShareEdit = True
		self.setButtonsEnabled()

	@utils.showWaitCursorDecorator
	def saveSettings(self):
		""" Save changes to database.
			Set _changesMade to True to ensure main window models are refreshed
			to pick up changes
		"""
		self._changesMade = True
		self.accountShareView.model().submitAll()
		index = self.accountCombo.currentIndex()
		if not self.accountCombo.model().submitAll():
			QtGui.QMessageBox.critical(self, 'Database Error',
				str(self.accountCombo.model().lastError()))
			self.revertChanges()
		self.accountCombo.setCurrentIndex(index)
		self._allowAccountShareEdit = True
		self.setButtonsEnabled()

