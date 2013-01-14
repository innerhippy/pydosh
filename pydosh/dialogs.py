from PyQt4 import QtCore, QtGui, QtSql
from ui_settings import Ui_settings
import enum
from models import AccountTableModel

class SettingsDialog(Ui_settings, QtGui.QWidget):
	def __init__(self, userId, parent=None):
		super(SettingsDialog, self).__init__(parent=parent)
		
		self.setAttribute(QtGui.Qt.WA_DeleteOnClose)
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
		self.accountsView.setSelectionBehavior(QAbstractItemView::SelectRows)
		self.accountsView.setSelectionMode(QAbstractItemView::ExtendedSelection)
		self.accountsView.sortByColumn(kAccountTypeColumn_AccountName, Qt::AscendingOrder)
		self.accountsView.resizeColumnsToContents()
		self.accountsView.horizontalHeader().setStretchLastSection(true)
		self.accountsView.setItemDelegate(new AccountDelegate(ui.accountsView))
	
		connect(model, SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)), ui.accountsView, SLOT(clearSelection()));
		connect(model, SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)), this, SLOT(enableCommit()));
		connect(model, SIGNAL(beforeInsert(QSqlRecord&)), this, SLOT(validateNewAccount(QSqlRecord&)));
	
		return model


SettingsModel*
SettingsDialog::loadBankCodes()
{
	SettingsModel* model = new CodeTableModel(this);

	model->setTable("codes");
	model->setEditStrategy(QSqlTableModel::OnManualSubmit);
	model->select();

	ui.codesView->setModel(model);
	ui.codesView->setColumnHidden(kCodeColumn_CodeId, true);
	ui.codesView->verticalHeader()->hide();
	ui.codesView->setSelectionBehavior(QAbstractItemView::SelectRows);
	ui.codesView->setSelectionMode(QAbstractItemView::ExtendedSelection);
	ui.codesView->sortByColumn(kCodeColumn_Code, Qt::AscendingOrder);
	ui.codesView->resizeColumnsToContents();
	ui.codesView->horizontalHeader()->setStretchLastSection(true);

	connect(model, SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)), ui.codesView, SLOT(clearSelection()));
	connect(model, SIGNAL(dataChanged(const QModelIndex&, const QModelIndex&)), this, SLOT(enableCommit()));

	return model;
}


void
SettingsDialog::searchCodes(const QString& text)
{
	if (!m_model)
		return;

	QString filter;

	if (!text.isEmpty())
		filter = QString("lower(code) like '%%%1%%' or lower(description) like '%%%1%%'").arg(text.toLower());

	m_model->setFilter(filter);
}


void SettingsDialog::validateNewAccount(QSqlRecord& record)
{
	QString error;

	if (record.value(kAccountTypeColumn_AccountName).toString().isEmpty())
		error = "Account name cannot be empty!";
	else if (record.value(kAccountTypeColumn_DateField).isNull())
		error = "Date field must be set!";
	else if (record.value(kAccountTypeColumn_DescriptionField).isNull())
		error = "Description field must be set!";
	else if (qAbs(record.value(kAccountTypeColumn_CurrencySign).toInt()) != 1)
		error = "Current sign value must be 1 or -1";
	else if (record.value(kAccountTypeColumn_DateFormat).toString().isEmpty())
		error = "Date format cannot be empty!";

	if (!error.isEmpty()) {
		QMessageBox::critical(this, tr("Account failed"), error, QMessageBox::Ok);

		// Trash the bad record
		record.clear();
	}
}


void
SettingsDialog::saveSettings()
{
	if (!m_model)
		return;

	if (!m_model->submitAll() && m_model->lastError().isValid()) {

		// If we've cleared the record from validateNewAccount() then the database error
		// will be empty. No need to issue a second error message
		if (!m_model->lastError().databaseText().isEmpty()) {
			QMessageBox::critical( this, tr("Error saving data"), m_model->lastError().text(), QMessageBox::Ok);
		}
		m_model->revertAll();
	}

	enableCommit(false);
}

void
SettingsDialog::cancelSettings() 
{
	if (!m_model)
		return;

	m_model->revertAll();
	enableCommit(false);
}

void SettingsDialog::enableCommit(bool enable)
{
	ui.saveButton->setEnabled(enable);
	ui.revertButton->setEnabled(enable);
}


void
SettingsDialog::addToModel()
{
	if (!m_model)
		return;

	int row = m_model->rowCount();
	m_model->insertRow(row);

	QModelIndex index = m_model->index(row, 1);
	m_view->setCurrentIndex(index);
	m_view->edit(index);
}


void
SettingsDialog::deleteFromModel()
{
	if (!m_model)
		return;

	QModelIndexList rows = m_view->selectionModel()->selectedRows();
	
	for (int i=0; i<rows.size(); i++) {
		QModelIndex index = rows.at(i);

		if (index.isValid()) {
			m_model->removeRows(index.row(), 1);
		}
	}

	m_view->clearSelection();
	enableCommit();
}

void 
SettingsDialog::showHelp()
{
	if (ui.optionsTab->currentIndex() == 0) {
		HelpBrowser::showPage("options.html#Bank_Codes");
	}
	else {
		HelpBrowser::showPage("options.html#Account_Types");
	}
}
