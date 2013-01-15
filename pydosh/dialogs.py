from PyQt4 import QtCore, QtGui, QtSql
from helpBrowser import HelpBrowser
from ui_settings import Ui_Settings
from ui_login import Ui_Login
from ui_tags import Ui_Tags
from utils import showWaitCursor
import enum
from database import db
from delegates import AccountDelegate
from models import AccountModel, TagModel

import pdb

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
		self.helpButton.clicked.connect(self.showHelp)

		self.enableCommit(False)

		model = QtSql.QSqlTableModel(self)
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
		self.view.setItemDelegate(AccountDelegate())

		model.dataChanged.connect(self.view.clearSelection)
		model.dataChanged.connect(self.__dataChanged)
		model.beforeInsert.connect(self.validateNewAccount)

		self.model = model

	def __dataChanged(self, left, right):
		self.enableCommit(True)

	def showHelp(self):
		browser = HelpBrowser(self)
		browser.showPage('options.htm')

	def validateNewAccount(self, record):
		error = ''

		if not record.value(enum.kAccountTypeColumn_AccountName).toString():
			error = "Account name cannot be empty!";
		elif record.value(enum.kAccountTypeColumn_DateField).isNull():
			error = "Date field must be set!";
		elif record.value(enum.kAccountTypeColumn_DescriptionField).isNull():
			error = "Description field must be set!";
		elif abs(record.value(enum.kAccountTypeColumn_CurrencySign).toInt()) != 1:
			error = "Current sign value must be 1 or -1";
		elif not record.value(enum.kAccountTypeColumn_DateFormat).toString():
			error = "Date format cannot be empty!";
	
		if error:
			QtGui.QMessageBox.critical(self, 'Account failed', error, QtGui.QMessageBox.Ok)
			# Trash the bad record
			record.clear()


	def saveSettings(self):

		if self.m_model.submitAll() and self.model.lastError().isValid():
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

		index = self.model.index(rowCount, 1)
		self.view.setCurrentIndex(index)
		self.view.exit(index)

	def deleteAccount(self):
		import pdb
		pdb.set_trace()
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
		db.connected.connect(self.setConnectionStatus)
		self.closeButton.clicked.connect(self.reject)
		self.helpButton.clicked.connect(self.showHelp)

		self.hostnameEdit.setText(db.hostname)
		self.databaseEdit.setText(db.database)
		self.usernameEdit.setText(db.username)
		self.passwordEdit.setText(db.password)
		self.portSpinBox.setValue(db.port)

		#TODO: remove!
		#self.activateConnection()

		self.setConnectionStatus()

	def setConnectionStatus(self):
		self.connectionButton.setText('Disconnect' if db.isConnected else 'Connect')
		
	def activateConnection(self):
		
		if db.isConnected:
			db.disconnect()
		else:
			db.database = self.databaseEdit.text()
			db.hostname = self.hostnameEdit.text()
			db.username = self.usernameEdit.text()
			db.password = self.passwordEdit.text()
			db.port = self.portSpinBox.value()

			if db.connect():
				self.accept()

	def showHelp(self):
		browser = HelpBrowser(self)
		browser.showPage('login.html')
		
		

class TagDialog(Ui_Tags, QtGui.QDialog):
	def __init__(self, recordIds, parent=None):
		super(TagDialog, self).__init__(parent=parent)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)
		QtSql.QSqlDatabase.database().transaction()
		self.tagView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.tagView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		#self.tagView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		self.deleteTagButton.setEnabled(False)
		# TODO: remove!
		#model = TagModel([4000,5819], self)
		model = TagModel(recordIds, self)
		model.setTable('tags')
		model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
		model.setFilter('userid=%d' % db.userId)
		model.select()
		
		self.tagView.setModel(model)
		self.tagView.setModelColumn(enum.kTagsColumn_TagName)

		self.accepted.connect(self.saveChanges)
		self.addTagButton.pressed.connect(self.addTag)
		self.deleteTagButton.pressed.connect(self.deleteTags)
		self.tagView.selectionModel().selectionChanged.connect(self.activateDeleteTagButton)
	
		self.helpButton.pressed.connect(self.showHelp)
		self.model = model


	def showHelp(self):
		browser = HelpBrowser(self)
		browser.showPage('main.html#Tags')

	def activateDeleteTagButton(self, selected):
		self.deleteTagButton.setEnabled(len(selected) > 0)

	def addTag(self):
		""" Add a new tag
		"""
		tagName, ok = QtGui.QInputDialog.getText(self, 'New Tag', 'Tag', QtGui.QLineEdit.Normal)

		if ok and tagName:
			if tagName in self.model:
				QtGui.QMessageBox.critical( self, 'Tag Error', 'Tag already exists!', QtGui.QMessageBox.Ok)
				return

			self.model.addTag(tagName)


	def deleteTags(self):
		for index in self.tagView.selectionModel().selectedIndexes():
			self.model.removeRows(index.row(), 1)

	@showWaitCursor
	def saveChanges(self):
		QtSql.QSqlDatabase.database().commit()
