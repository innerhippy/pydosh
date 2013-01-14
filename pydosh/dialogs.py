from PyQt4 import QtCore, QtGui, QtSql
from ui_settings import Ui_Settings
from ui_login import Ui_Login
import enum
from database import db
from models import AccountTableModel

class SettingsDialog(Ui_Settings, QtGui.QWidget):
	def __init__(self, userId, parent=None):
		super(SettingsDialog, self).__init__(parent=parent)
		
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)
	
		self.optionsTab.currentChanged.connect(self.loadTabPage)
#	connect (ui.saveButton, SIGNAL(clicked()), this, SLOT(saveSettings()));
#	connect (ui.revertButton, SIGNAL(clicked()), this, SLOT(cancelSettings()));
#	connect (ui.closeButton, SIGNAL(clicked()), this, SLOT(close()));
#	connect (ui.searchEdit, SIGNAL(textChanged(const QString&)), this, SLOT(searchCodes(const QString&)));
#	connect (ui.addButton, SIGNAL(clicked()), this, SLOT(addToModel()));
#	connect (ui.deleteButton, SIGNAL(clicked()), this, SLOT(deleteFromModel()));
#	connect (ui.helpButton, SIGNAL(clicked()), this, SLOT(showHelp()));

		self.saveButton.setEnabled(False)
		self.revertButton.setEnabled(False)
		self.model = self.loadAccountTypes()
		self.loadTabPage(self.optionsTab.currentIndex())

#void SettingsDialog::loadTabPage(int currentTab)
#{
#
#	if (currentTab == 0) {
#		// Codes tab
#		delete m_model;
#		m_model = loadBankCodes();
#		m_view = ui.codesView;
#	}
#	else if (currentTab == 1) {
#		// Accounts tab
#		delete m_model;
#		m_model = loadAccountTypes();
#		m_view = ui.accountsView;
#	}
#}

	def loadAccountTypes(self):
		model = AccountTableModel(self)
	
		model.setTable('accounttypes')
		model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
		model.select()
	
		self.accountsView.setModel(model)
		self.accountsView.setColumnHidden(enum.kAccountTypeColumn_AccountTypeId, True)
		self.accountsView.verticalHeader().hide()
		self.accountsView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.accountsView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.accountsView.sortByColumn(enum.kAccountTypeColumn_AccountName, QtCore.Qt.AscendingOrder)
		self.accountsView.resizeColumnsToContents()
		self.accountsView.horizontalHeader().setStretchLastSection(True)
		#self.accountsView.setItemDelegate(AccountDelegate(self.accountsView))

		model.dataChanged.connect(self.accountsView.clearSelection)
		model.dataChanged.connect(self.enableCommit)
		model.beforeInsert.connect(self.validateNewAccount)

		return model


#SettingsModel*
#SettingsDialog::loadBankCodes()
#{
#	SettingsModel* model = new CodeTableModel(this);
#
#	model->setTable("codes");
#	model->setEditStrategy(QSqlTableModel::OnManualSubmit);
#	model->select();
#
#	ui.codesView->setModel(model);
#	ui.codesView->setColumnHidden(kCodeColumn_CodeId, true);
#	ui.codesView->verticalHeader()->hide();
#	ui.codesView->setSelectionBehavior(QAbstractItemView::SelectRows);
#	ui.codesView->setSelectionMode(QAbstractItemView::ExtendedSelection);
#	ui.codesView->sortByColumn(kCodeColumn_Code, Qt::AscendingOrder);
#	ui.codesView->resizeColumnsToContents();
#	ui.codesView->horizontalHeader()->setStretchLastSection(true);
#
#	connect(model, SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)), ui.codesView, SLOT(clearSelection()));
#	connect(model, SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)), this, SLOT(enableCommit()));
#
#	return model
#}


#void
#SettingsDialog::searchCodes(const QString& text)
#{
#	if (!m_model)
#		return;
#
#	QString filter;
#
#	if (!text.isEmpty())
#		filter = QString("lower(code) like '%%%1%%' or lower(description) like '%%%1%%'").arg(text.toLower());
#
#	m_model->setFilter(filter);
#}

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


#void
#SettingsDialog::saveSettings()
#{
#	if (!m_model)
#		return;
#
#	if (!m_model->submitAll() && m_model->lastError().isValid()) {
#
#		// If we've cleared the record from validateNewAccount() then the database error
#		// will be empty. No need to issue a second error message
#		if (!m_model->lastError().databaseText().isEmpty()) {
#			QMessageBox::critical( this, tr("Error saving data"), m_model->lastError().text(), QMessageBox::Ok);
#		}
#		m_model->revertAll();
#	}
#
#	enableCommit(false);
#}
#
#void
#SettingsDialog::cancelSettings() 
#{
#	if (!m_model)
#		return;
#
#	m_model->revertAll();
#	enableCommit(false);
#}
#
#void SettingsDialog::enableCommit(bool enable)
#{
#	ui.saveButton->setEnabled(enable);
#	ui.revertButton->setEnabled(enable);
#}
#
#
#void
#SettingsDialog::addToModel()
#{
#	if (!m_model)
#		return;
#
#	int row = m_model->rowCount();
#	m_model->insertRow(row);
#
#	QModelIndex index = m_model->index(row, 1);
#	m_view->setCurrentIndex(index);
#	m_view->edit(index);
#}
#
#
#void
#SettingsDialog::deleteFromModel()
#{
#	if (!m_model)
#		return;
#
#	QModelIndexList rows = m_view->selectionModel()->selectedRows();
#	
#	for (int i=0; i<rows.size(); i++) {
#		QModelIndex index = rows.at(i);
#
#		if (index.isValid()) {
#			m_model->removeRows(index.row(), 1);
#		}
#	}
#
#	m_view->clearSelection();
#	enableCommit();
#}
#
#void 
#SettingsDialog::showHelp()
#{
#	if (ui.optionsTab->currentIndex() == 0) {
#		HelpBrowser::showPage("options.html#Bank_Codes");
#	}
#	else {
#		HelpBrowser::showPage("options.html#Account_Types");
#	}
#}

class LoginDialog(Ui_Login, QtGui.QDialog):
	def __init__(self, parent=None):
		super(LoginDialog, self).__init__(parent=parent)
	
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)

		self.passwordEdit.setEchoMode(QtGui.QLineEdit.Password)

		self.connectionButton.clicked.connect(self.activateConnection)
#		connect (&Database::Instance(), SIGNAL(connected(bool, const QString&)), this, SLOT(setConnectionStatus(bool)));
		self.closeButton.clicked.connect(self.reject)
#		self.helpButton.clicked.connect(self.showHelp)

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

