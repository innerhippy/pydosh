from PyQt4 import QtCore, QtGui, QtSql
from helpBrowser import HelpBrowser
from ui_settings import Ui_Settings
from ui_login import Ui_Login
from ui_tags import Ui_Tags
from utils import showWaitCursor
import enum
from database import db
from delegates import AccountDelegate
from models import AccountTableModel

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
	def __init__(self, recordids, parent=None):
		super(TagDialog, self).__init__(parent=parent)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)
	
		self.tagListWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.deleteTagButton.setEnabled(False)
	
		query = QtSql.QSqlQuery("""
					SELECT tagname, tagid, (
						SELECT COUNT(*)
						FROM recordtags
						WHERE tagid=tags.tagid
						AND recordid in (%s)
						)
					FROM tags
					WHERE userid=%d ORDER BY tagname
				""" % ( recordids.join(','), db.userId))
	
		if query.lastError().isValid():
			QtGui.QMessageBox.critical( self, 'Tag Error', query.lastError().text(), QtGui.QMessageBox.Ok)
			print query.lastQuery().replace('\n', ' ')

		while query.next():
			
			item = QtGui.QListWidgetItem(query.value(0).toString())
			val, ok = query.value(1).toInt()
			if not ok:
				continue

			item.setData(QtCore.Qt.UserRole, val)

			if query.value(2).toInt() == len(recordids):
				item.setCheckState(QtCore.Qt.Checked)
			elif query.value(2).toInt() == 0:
				item.setCheckState(QtCore.Qt.Unchecked)
			else:
				item.setCheckState(QtCore.Qt.PartiallyChecked)
			self.tagListWidget.addItem(item)

		self.accepted.connect(self.saveTags)
		self.addTagButton.pressed.connect(self.addTag)
		self.deleteTagButton.pressed.connect(self.setDeleteTags)
		self.tagListWidget.selectionModel().selectionChanged.connect(self.activateDeleteTagButton)
	
		self.helpButton.pressed.connect(self.showHelp)


	def showHelp(self):
		browser = HelpBrowser(self)
		browser.showPage('main.html#Tags')

	def activateDeleteTagButton(self):
		self.deleteTagButton.setEnabled(len(self.tagListWidget.selectionModel().selectedRows()))

	def addTag(self):

		tagname, ok = QtGui.QInputDialog.getText(self, 'Create New Tag', 'Tag', QtGui.QLineEdit.Normal)
		if ok and tagname:
			query = QtSql.QSqlQuery()
			query.prepare('INSERT INTO tags (tagname, userid) VALUES (?, ?)')
			query.addBindValue(tagname)
			query.addBindValue(db.userId)
			query.exec_()

			if query.lastError().isValid():
				QtGui.QMessageBox.critical( self, 'Tag Error', query.lastError().text(), QtGui.QMessageBox.Ok)
				return

			#  lastInsertId does not seem to work with psql - do it the hard way.
			query.prepare('SELECT tagid from tags WHERE tagname=? AND userid=?')
			query.addBindValue(tagname)
			query.addBindValue(db.userId)
			query.exec_()
			query.next()

			item = QtGui.QListWidgetItem(tagname)
			item.setData(QtCore.Qt.UserRole, query.value(0).toInt())
			item.setCheckState(QtCore.Qt.Checked)
			self.tagListWidget.addItem(item)
			
	def setDeleteTags(self):
		for item in self.tagListWidget.selectedItems():
			font = QtGui.QFont(item.font())
			font.setStrikeOut(True)
			item.setFont(font)

	def deleteTags(self):
		tagsToDelete = []

		for i in xrange(self.tagListWidget.count()):
			item = self.tagListWidget.item(i)
			if item.font().strikeOut():
				tagsToDelete.append(str(item.data(QtCore.Qt.UserRole).toString()))

		if tagsToDelete:
			query = QtSql.QSqlQuery('DELETE FROM tags WHERE tagid IN (%s)' % ','.join(tagsToDelete))
			query.next()

	@showWaitCursor
	def saveTags(self):

		self.deleteTags()

		pdb.set_trace()
#		for (int i=0; i< self.tagListWidget->count(); i++) {
#			QListWidgetItem* item = self.tagListWidget->item(i);
"""			
			if (item->font().strikeOut()) {
				// No point, they've gone.
				continue;
			}
			
			int tagId = item->data(Qt::UserRole).toInt();
	
			if (item->checkState() == Qt::Unchecked) {
	
				QSqlQuery query(QString ("DELETE FROM recordtags where tagid=%1 and recordid in (%2)")
						.arg(tagId)
						.arg(m_recordids.join(",")));
			}
			else if (item->checkState() == Qt::Checked) {
	
				QStringList existingRecs;
				QSqlQuery query(QString("SELECT recordid from recordtags where tagid=%1").arg(tagId));
	
				while (query.next()) {
					existingRecs << query.value(0).toString();
				}
	
				for (int i=0; i< m_recordids.size(); i++) {
	
					if (!existingRecs.contains(m_recordids.at(i))) {
	
						QSqlQuery query (QString("INSERT INTO recordtags (recordid, tagid) VALUES (%1, %2)")
								.arg(m_recordids.at(i))
								.arg(tagId));
	
						if (query.lastError().isValid()) {
							QApplication::restoreOverrideCursor();
							QMessageBox::critical( this, tr("Tag Error"), query.lastError().text(), QMessageBox::Ok);
	     					return;
						}
					}
				}
			}
			else {
				// partial check - do nothing as values have not changed!
			}
		}
		QApplication::restoreOverrideCursor();
"""

