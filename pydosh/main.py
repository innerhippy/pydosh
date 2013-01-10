from PyQt4 import QtGui, QtCore

from Ui_pydosh import Ui_pyDosh

"""
MainWindow::MainWindow(QWidget *parent, Qt::WFlags flags) :
	QMainWindow(parent, flags),
	m_model(0)
{
	setAttribute(Qt::WA_DeleteOnClose);
	ui.setupUi(this);

	ui.checkedCombo->addItem("all", kCheckedStatus_All);
	ui.checkedCombo->addItem("checked", kCheckedStatus_Checked);
	ui.checkedCombo->addItem("unchecked", kCheckedStatus_UnChecked);

	ui.inoutCombo->addItem("all", kInOutStatus_All);
	ui.inoutCombo->addItem("money in", kInOutStatus_In);
	ui.inoutCombo->addItem("money out", kInOutStatus_Out);

//	ui.startDateCombo->setSizeAdjustPolicy(QComboBox::AdjustToContents);
//	ui.endDateCombo->setSizeAdjustPolicy(QComboBox::AdjustToContents);

	ui.tagEditButton->setEnabled(false);
	ui.toggleCheckButton->setEnabled(false);

	connect (ui.checkedCombo, SIGNAL(currentIndexChanged (int)), this, SLOT(setFilters()));
	connect (ui.inoutCombo, SIGNAL(currentIndexChanged (int)), this, SLOT(setFilters()));
	connect (ui.typeCombo, SIGNAL(currentIndexChanged (int)), this, SLOT(setFilters()));
	connect (ui.accountCombo, SIGNAL(currentIndexChanged (int)), this, SLOT(setFilters()));
	connect (ui.descEdit, SIGNAL(textChanged(const QString&)), this, SLOT(setFilters()));
	connect (ui.amountEdit, SIGNAL(textChanged(const QString&)), this, SLOT(setFilters()));
	connect (ui.amountEdit, SIGNAL(controlKeyPressed(int)), this, SLOT(controlKeyPressed(int)));
	connect (ui.tagEdit, SIGNAL(editingFinished()), this, SLOT(setFilters()));
	connect (ui.startDateEdit, SIGNAL(dateChanged(const QDate&)), this, SLOT(setFilters()));
	connect (ui.endDateEdit, SIGNAL(dateChanged(const QDate&)), this, SLOT(setFilters()));
	connect (ui.toggleCheckButton, SIGNAL(clicked()), this, SLOT(toggleSelected()));
	connect (ui.dateRangeCheckbox, SIGNAL(stateChanged(int)), this, SLOT(setEndDate(int)));
	connect (ui.reloadButton, SIGNAL(clicked()), this, SLOT(reset()));
	connect (ui.tableView, SIGNAL(clicked(const QModelIndex&)), this, SLOT(itemChecked(const QModelIndex&)));
	connect (ui.tagEditButton, SIGNAL(pressed()), this, SLOT(addTagButtonPressed()));

	connect (&Database::Instance(), SIGNAL(connected(bool, const QString&)), this, SLOT(setConnectionStatus(bool, const QString&)));

	QValidator *amountValidator = new QRegExpValidator(QRegExp("[<>=0-9.]*"), this);
	ui.amountEdit->setValidator(amountValidator);

	ui.startDateEdit->setCalendarPopup(true);
	ui.endDateEdit->setCalendarPopup(true);

	addActions();

	ui.inTotalLabel->setFrameStyle(QFrame::StyledPanel | QFrame::Sunken);
	ui.outTotalLabel->setFrameStyle(QFrame::StyledPanel | QFrame::Sunken);
	ui.recordCountLabel->setFrameStyle(QFrame::StyledPanel | QFrame::Sunken);

	setConnectionStatus(Database::Instance().isConnected(), Database::Instance().connectionDetails());

	loadData();
}


MainWindow::~MainWindow()
{
}

void MainWindow::show() {
	/* I'm sure there's a better way of doing this..
	 * need to call resizeColumnsToContents after show() so that the
	 * viewport height can be used to determine which rows to consider.
	 * Otherwise every row in the model will be used to calculate the
	 * column width (it seems) which is ugly.
	 */
	QMainWindow::show();
	ui.tableView->resizeColumnsToContents();
}

void MainWindow::addActions()
{
	QAction* quitAction = new QAction(tr("&Quit"),this);
	quitAction->setShortcut(tr("Alt+q"));
	quitAction->setStatusTip(tr("Exit the program"));
	quitAction->setIcon(QIcon(":/icons/exit.png"));
	connect(quitAction, SIGNAL(triggered()),this, SLOT(close()));

	QAction* settingsAction = new QAction(tr("&Settings"),this);
	settingsAction->setShortcut(tr("Alt+s"));
	settingsAction->setStatusTip(tr("Change the settings"));
	settingsAction->setIcon(QIcon(":/icons/wrench.png"));
	connect(settingsAction, SIGNAL(triggered()),this, SLOT(settingsDialog()));

	QAction* loginAction = new QAction(tr("&Login"),this);
	loginAction->setShortcut(tr("Alt+l"));
	loginAction->setStatusTip(tr("Login"));
	loginAction->setIcon(QIcon(":/icons/disconnect.png"));
	connect(loginAction, SIGNAL(triggered()),this, SLOT(loginDialog()));

	QAction* importAction = new QAction(tr("&Import"),this);
	importAction->setShortcut(tr("Alt+i"));
	importAction->setStatusTip(tr("Import Bank statements"));
	importAction->setIcon(QIcon(":/icons/import.png"));
	connect(importAction, SIGNAL(triggered()),this, SLOT(importDialog()));

	QAction* aboutAction = new QAction(tr("&About"),this);
	aboutAction->setStatusTip(tr("About"));
	aboutAction->setIcon(QIcon(":/icons/help.png"));
	connect(aboutAction, SIGNAL(triggered()),this, SLOT(showAbout()));
	
	QAction* helpAction = new QAction(tr("&Help"),this);
	helpAction->setStatusTip(tr("Help"));
	helpAction->setIcon(QIcon(":/icons/help.png"));
	connect(helpAction, SIGNAL(triggered()),this, SLOT(showHelp()));

	addAction(settingsAction);
	addAction(importAction);
	addAction(quitAction);
	addAction(aboutAction);
	addAction(helpAction);
	addAction(loginAction);

	// File menu
	QMenu *fileMenu = menuBar()->addMenu(tr("&Tools"));
	fileMenu->addAction(loginAction);
	fileMenu->addAction(settingsAction);
	fileMenu->addAction(importAction);
	fileMenu->addAction(quitAction);

	// Help menu
	QMenu *helpMenu = menuBar()->addMenu(tr("&Help"));
	helpMenu->addAction(aboutAction);
	helpMenu->addAction(helpAction);
}

void MainWindow::showHelp()
{
	HelpBrowser::showPage("main.html");
}

void
MainWindow::showAbout()
{
	QMessageBox::about(this,
			tr("About doshLogger"),
			tr(
					"<html><p><h2>doshlogger</h2></p>"
					"<p>version "
					APPLICATION_VERSION
					"</p>"
					"<p>by Will Hall <a href=\"mailto:dev@innerhippy.com\">dev@innerhippy.com</a><br>"
					"Copywrite (c) 2010. Will Hall </p>"
					"<p>Written using Qt"
					QT_VERSION_STR
					"<br>"
#if defined(__GNUC__)
					"Compiled using GCC"
					__VERSION__
					"<p>"
					"<a href=\"http://www.innerhippy.com\">www.innerhippy.com</a></p>"
					"enjoy!</html>"
#endif
			));
}

void MainWindow::setConnectionStatus(bool isConnected, const QString& status)
{
	if (isConnected) {
		ui.connectionStatusText->setText(QString("connected to %1").arg(status));
		ui.connectionStatusIcon->setPixmap(QPixmap(QString::fromUtf8(":/icons/thumb_up.png")));
	}
	else {
		ui.connectionStatusText->setText("not connected");
		ui.connectionStatusIcon->setPixmap(QPixmap(QString::fromUtf8(":/icons/thumb_down.png")));
		delete m_model;
		m_model=0;
		displayRecordCount();
		ui.tableView->setModel(0);
	}
}

void
MainWindow::displayRecordCount()
{
	int numRecords=0;
	int totalRecords=0;
	double inTotal=0.0;
	double outTotal=0.0;

	if (m_model) {
		numRecords = m_model->rowCount();

		QSqlQuery query(QString(
					"SELECT COUNT(*) FROM records WHERE userid=%1")
					.arg(Database::Instance().userId()));

		query.next();
		totalRecords = query.value(0).toInt();
		for (int i=0; i<m_model->rowCount(); i++) {
			double amount = m_model->record(i).value(kRecordColumn_Amount).toDouble();
			if (amount > 0.0)
				inTotal += amount;
			else
				outTotal += fabs(amount);
		}
	}
	ui.inTotalLabel->setText(QString("%L1").arg(inTotal, 0, 'f', 2));
	ui.outTotalLabel->setText(QString("%L1").arg(outTotal, 0, 'f', 2));
	ui.recordCountLabel->setText(QString("%L1 / %L2 ").arg(numRecords).arg(totalRecords));
}

void
MainWindow::loadData()
{
	if (!Database::Instance().isConnected())
		return;

	QApplication::setOverrideCursor(Qt::WaitCursor);

	blockAllSignals(true);

	delete m_model;
	m_model = new SqlTableModel(this);
	m_model->setTable("records");
	m_model->setEditStrategy(QSqlTableModel::OnFieldChange);
	m_model->select();

	SortProxyModel* proxy = new SortProxyModel(this);
	proxy->setSourceModel(m_model);
	proxy->setFilterKeyColumn(-1);

	ui.tableView->setEditTriggers(QAbstractItemView::DoubleClicked| QAbstractItemView::SelectedClicked);

	ui.tableView->setModel(proxy);
	ui.tableView->verticalHeader()->hide();
	ui.tableView->setEditTriggers(QAbstractItemView::NoEditTriggers);
	ui.tableView->setSelectionMode(QAbstractItemView::ExtendedSelection);
	ui.tableView->setSelectionBehavior(QAbstractItemView::SelectRows);
	ui.tableView->setColumnHidden(kRecordColumn_RecordId, true);
	ui.tableView->setColumnHidden(kRecordColumn_CheckDate, true);
	ui.tableView->setColumnHidden(kRecordColumn_RawData, true);
	ui.tableView->setColumnHidden(kRecordColumn_User, true);
	ui.tableView->setColumnHidden(kRecordColumn_InsertDate, true);
	ui.tableView->setSortingEnabled(true);
	ui.tableView->sortByColumn(kRecordColumn_Date, Qt::DescendingOrder);
 	ui.tableView->horizontalHeader()->setStretchLastSection(true);
	connect(ui.tableView->selectionModel(), SIGNAL(selectionChanged(const QItemSelection&, const QItemSelection&)),
			this, SLOT(activateButtons()));

	reset();

	QApplication::restoreOverrideCursor();
	blockAllSignals(false);
}

void MainWindow::loadTags()
{
	QStringList tagList;
	QSqlQuery query(QString(
			"SELECT tagname FROM tags WHERE userid=%1")
			.arg(Database::Instance().userId()));

	while (query.next()) {
		tagList << query.value(0).toString();
	}

	QCompleter* completer = new QCompleter(tagList, ui.tagEdit);
	ui.tagEdit->setCompleter(completer);
	ui.tagEdit->completer()->setCaseSensitivity(Qt::CaseInsensitive);
	ui.tagEdit->completer()->setCompletionMode(QCompleter::PopupCompletion);
	
	connect (completer, SIGNAL(activated(const QString&)), this, SLOT(setFilters()));
}

void 
MainWindow::blockAllSignals(bool block)
{
	ui.accountCombo->blockSignals(block);
	ui.typeCombo->blockSignals(block);
	ui.dateRangeCheckbox->blockSignals(block);
	ui.descEdit->blockSignals(block);
	ui.amountEdit->blockSignals(block);
	ui.startDateEdit->blockSignals(block);
	ui.endDateEdit->blockSignals(block);
}

void 
MainWindow::setEndDate(int state)
{
	ui.endDateEdit->setEnabled( state == Qt::Checked );
	setFilters();
}

void
MainWindow::toggleSelected()
{
	toggleChecked (getSelectedRecordIds());
}

void MainWindow::toggleChecked(const QStringList& recordids)
{
	if (!recordids.size())
		return;
		
	QSqlQuery query(QString (
			"UPDATE records SET checked=abs(checked -1),checkdate='%1' "
			"WHERE recordid IN (%2)")
			.arg(QDateTime::currentDateTime().toString("yyyy-MM-dd hh:mm:ss"))
			.arg(recordids.join(",")));

	query.next();
	
	if (query.lastError().isValid()) {
		QMessageBox::critical( this, tr("DB Error"), query.lastError().text(), QMessageBox::Ok);
		return;
	}

	saveTableState();
	m_model->select();
	restoreTableState();

	if (m_model->rowCount() == 0) {
		// Smart focus - if we have no records showing then reset the last
		// search filter and set focus
		QString descFilter = ui.descEdit->text();
		QString amountFilter = ui.amountEdit->text();
		QString tagFilter = ui.tagEdit->text();

		if (!descFilter.isEmpty() && amountFilter.isEmpty() && tagFilter.isEmpty() ) {
			ui.descEdit->clear();
			ui.descEdit->setFocus(Qt::OtherFocusReason);
		}
		else if (!amountFilter.isEmpty() && descFilter.isEmpty() && tagFilter.isEmpty()) {
			ui.amountEdit->clear();
			ui.amountEdit->setFocus(Qt::OtherFocusReason);
		}
		else if (!tagFilter.isEmpty() && descFilter.isEmpty() && amountFilter.isEmpty()) {
			ui.amountEdit->clear();
			ui.amountEdit->setFocus(Qt::OtherFocusReason);
		}
	}
	displayRecordCount();
}

void
MainWindow::itemChecked(const QModelIndex& index)
{
	if (!m_model)
		return;

	if (index.column() != kRecordColumn_Checked)
		return;

	const QSortFilterProxyModel* proxyModel = qobject_cast<const QSortFilterProxyModel*>(ui.tableView->model());
	Q_ASSERT(proxyModel);

	toggleChecked (QStringList() << m_model->record(proxyModel->mapToSource(index).row()).value(kRecordColumn_RecordId).toString());
}

void
MainWindow::activateButtons()
{
	QItemSelectionModel* model = ui.tableView->selectionModel();
	bool enable=false;

	if (model) {
		enable = model->selectedRows().size() > 0;
	}
	
	ui.tagEditButton->setEnabled(enable);
	ui.toggleCheckButton->setEnabled(enable);
	
}

QStringList MainWindow::getSelectedRecordIds() const
{
	// get recordids from all selected rows
	QItemSelectionModel* selectionModel = ui.tableView->selectionModel();
	Q_ASSERT(selectionModel);

	const QSortFilterProxyModel* proxyModel = qobject_cast<const QSortFilterProxyModel*>(ui.tableView->model());
	Q_ASSERT(proxyModel);

	QStringList recordids;
	QModelIndexList indexList = selectionModel->selectedRows();

	for (int i=0; i<indexList.size(); i++) {
		recordids << m_model->record(proxyModel->mapToSource(indexList.at(i)).row()).value(kRecordColumn_RecordId).toString();
	}

	return recordids;
}

void
MainWindow::addTagButtonPressed()
{
	QStringList recordids = getSelectedRecordIds();

	TagDialog* dialog = new TagDialog(recordids, this);

	if (dialog->exec()) {
		setFilters();
		loadTags();
	}
}

void
MainWindow::saveTableState()
{
	m_visibleRow = ui.tableView->indexAt(QPoint(5,5));
}


void
MainWindow::restoreTableState()
{
	// Restore view position
	if(m_visibleRow.isValid()) {
		ui.tableView->scrollTo(m_visibleRow, QAbstractItemView::PositionAtTop);
	}
}



void
MainWindow::settingsDialog()
{
	SettingsDialog* dialog = new SettingsDialog(this);
	dialog->exec();
	setFilters();
}

void
MainWindow::loginDialog()
{
	LoginDialog* dialog = new LoginDialog(this);

	if (dialog->exec()) {
		loadData();
	}
}

void
MainWindow::importDialog()
{
	if (!Database::Instance().isConnected())
		return;

	QComboBox* combo = new QComboBox;
	combo->addItem("None");

	QSqlQuery query(
			"SELECT accountname, accounttypeid "
			"FROM accounttypes "
			"ORDER BY accountname");

	while (query.next()) {
		// Store the accounttypeid in the userData field
		combo->addItem(query.value(0).toString(), query.value(1).toInt());
	}

	// find the previous accounttype that was used (if any)
	QSettings settings;
	QString accounttype = settings.value("options/importaccounttype").toString();

	int index = combo->findText(accounttype);

	if (index != -1)
		combo->setCurrentIndex(index);
	else
		combo->setCurrentIndex(0);

	QLabel* label = new QLabel("Account type:");
	QString importDir = settings.value("options/importdirectory").toString();

	if (importDir.isEmpty()) {
		importDir = QDir::homePath();
	}

	QFileDialog* fd = new QFileDialog(this, tr("Open File"), importDir, "*.csv");
	fd->setFileMode(QFileDialog::ExistingFiles);
	fd->setOption(QFileDialog::DontUseNativeDialog);

	QLayout* layout = fd->layout();
	QGridLayout* gridbox = qobject_cast<QGridLayout*>(layout);

	if (gridbox) {
		gridbox->addWidget(label);
		gridbox->addWidget(combo);
	}

	if (!fd->exec())
		return;

	QVariant accountTypeId = combo->itemData(combo->currentIndex(), Qt::UserRole);
	QString accountName = combo->itemData(combo->currentIndex(), Qt::DisplayRole).toString();

	// Save the settings for next time
	settings.setValue("options/importaccounttype", accountName);
	settings.setValue("options/importdirectory", fd->directory().absolutePath());

	if (!accountTypeId.isValid()) {
		QMessageBox::critical( this, tr("Import Error"), tr("No Account Type given!"), QMessageBox::Ok);
		return;
	}

	CSVDecoder decoder(accountName, fd->selectedFiles());

	if (!decoder.isValid()) {
		QMessageBox::critical( this, tr("Import Error"), decoder.error(), QMessageBox::Ok);
		return;
	}

	ImportDialog* dialog = new ImportDialog(decoder.records(), accountTypeId.toInt(), this);

	QStringList fileNames;
	for (int i=0; i < fd->selectedFiles().size(); i++) {
		fileNames << QFileInfo(fd->selectedFiles().at(i)).fileName();
	}

	dialog->setWindowTitle(fileNames.join(", "));

	if (dialog->exec()) {
		reset();
	}
}

void
MainWindow::populateCodes()
{
	ui.typeCombo->clear();
	ui.typeCombo->addItem("all");

	QSqlQuery query(
			"SELECT DISTINCT description "
			"FROM codes "
			"ORDER BY description ASC");

	while (query.next()) {
		ui.typeCombo->addItem(query.value(0).toString());
	}
}

void
MainWindow::populateAccounts()
{
	ui.accountCombo->clear();
	ui.accountCombo->addItem("all");

	// Only pull in account types used by this user
	QSqlQuery query(QString(
			"SELECT DISTINCT at.accountname, at.accounttypeid "
			"FROM accounttypes at "
			"INNER JOIN records r ON r.accounttypeid=at.accounttypeid "
			"WHERE r.userid=%1 "
			"ORDER BY at.accountname").arg(Database::Instance().userId()));

	while (query.next()) {
		// Store the accounttypeid in the userData field
		ui.accountCombo->addItem(query.value(0).toString(), query.value(1).toInt());
	}
}

void MainWindow::populateDates()
{
//	ui.startDateCombo->clear();
//	ui.endDateCombo->clear();

	QSqlQuery query( QString(
			"SELECT MIN(date), MAX(date) "
			"FROM records "
			"WHERE userid=%1").arg(Database::Instance().userId()));

	if (query.next()) {
		QDate startDate = query.value(0).toDate();
		QDate endDate = query.value(1).toDate();

		ui.startDateEdit->setDateRange(startDate, endDate);
		ui.endDateEdit->setDateRange(startDate, endDate);

		qDebug() << startDate << endDate;

		ui.endDateEdit->setDate(ui.startDateEdit->maximumDate());
		ui.startDateEdit->setDate(ui.endDateEdit->date().addYears(-1));

		qDebug() << "set as" <<  ui.startDateEdit->date() << ui.endDateEdit->date();
	}
}

void MainWindow::reset()
{
	if (!Database::Instance().isConnected() || !m_model)
		return;

	blockAllSignals(true);
	populateAccounts();
	populateDates();
	populateCodes();
	loadTags();

	ui.checkedCombo->setCurrentIndex(0);
	ui.typeCombo->setCurrentIndex(0);
	ui.accountCombo->setCurrentIndex(0);

	ui.inoutCombo->setCurrentIndex(0);
	ui.amountEdit->clear();
	ui.descEdit->clear();
	ui.tagEdit->clear();
	ui.dateRangeCheckbox->setCheckState(Qt::Checked);
	ui.endDateEdit->setEnabled(true);
	ui.tableView->sortByColumn(kRecordColumn_Date, Qt::DescendingOrder);

	blockAllSignals(false);

	setFilters();
}

void MainWindow::controlKeyPressed(int key) {
	// control key has been pressed - if we have a single row displayed, then toggle the status
	if (m_model && m_model->rowCount() == 1) {
		if (key == Qt::Key_Space) {
			toggleChecked(QStringList(m_model->record(0).value(kRecordColumn_RecordId).toString()));
		}
	}
}

void MainWindow::setFilters()
{
	if (!m_model || !Database::Instance().isConnected())
		return;

	qDebug() << "SETFILTER" << sender();
	/*
	 * User filter
	 */
	QString filter = QString("records.userid=%1").arg(Database::Instance().userId());

	/*
	 * Account filter
	 */
	QVariant accountNo = ui.accountCombo->itemData(ui.accountCombo->currentIndex(), Qt::UserRole);

	if (accountNo.isValid()) {
		filter += QString(" AND records.accounttypeid=%1").arg(accountNo.toInt());
	}

	/*
	 * filter on dates
	 */
	QDate startDate = ui.startDateEdit->date();
	QDate endDate = ui.endDateEdit->date();

	if (ui.dateRangeCheckbox->checkState() == Qt::Unchecked) {
		endDate = startDate;
	}

	if (startDate.isValid() && endDate.isValid()) {
		filter += QString(
				" AND date >= '%1' AND date < '%2' ")
				.arg(startDate.toString(Qt::ISODate))
				.arg(endDate.addMonths(1).toString(Qt::ISODate));
	}

	/*
	 * filter on code
	 */
	if (ui.typeCombo->currentIndex()) {
		filter += QString(" AND codes.description ='%1'").arg(ui.typeCombo->currentText());
	}

	/*
	 * filter on checked status
	 */
	switch (static_cast<eCheckedState>(ui.checkedCombo->itemData(ui.checkedCombo->currentIndex(), Qt::UserRole).toInt())) {
		case kCheckedStatus_Checked:
			filter += QString(" AND checked=1");
			break;
		case kCheckedStatus_UnChecked:
			filter += QString(" AND checked=0");
			break;
		default:
			break;
	}

	// Filter on money coming in or going out
	switch (static_cast<eCheckedState>(ui.inoutCombo->itemData(ui.inoutCombo->currentIndex(), Qt::UserRole).toInt())) {
		case kInOutStatus_In:
			filter += QString(" AND amount > 0");
			break;
		case kInOutStatus_Out:
			filter += QString(" AND amount < 0");
			break;
		default:
			break;
	}

	/*
	 * filter on description
	 */
	QString descFilter = ui.descEdit->text();
	if (!descFilter.isEmpty()) {
		filter += QString(" AND lower(records.description) LIKE lower('%%1%')").arg(descFilter);
	}

	/*
	 * filter on amount. May contain operators < > <= or >=
	 */
	QString amountFilter = ui.amountEdit->text();
	if (!amountFilter.isEmpty()) {
		// looks like we have operators!
		if (amountFilter.contains(QRegExp("[<>=]+"))) {

			// Test for valid operator and amount
			QRegExp rx("^(=|>|<|>=|<=)([\\.\\d+]+)");
			if (amountFilter.contains(rx)) {
				filter += QString(" AND abs(amount) %1 %2").arg(rx.cap(1), rx.cap(2));
			}
			else {
				// Input not complete yet.
				return;
			}
		}
		else {
			// No operator supplied - treat amount as a string
			filter += QString(" AND (CAST(amount AS char(10)) LIKE '%1%' OR CAST(amount AS char(10)) LIKE '-%1%')").arg(amountFilter);
		}
	}

	/*
	 * filter on tags
	 */
	QString tag = ui.tagEdit->text();

	if (!tag.isEmpty()) {
		filter += QString(" AND records.recordid IN "
				"(SELECT recordid from recordtags rt "
				"JOIN tags t ON t.tagid=rt.tagid "
				"WHERE t.tagname ='%1')").arg(tag);
	}

	/*
	 * Apply the filter with a pretty daisy wheel!
	 */
	QApplication::setOverrideCursor(Qt::WaitCursor);

	m_model->setFilter(filter);

	qDebug() << m_model->query().lastQuery();

	displayRecordCount();

	ui.tableView->resizeColumnsToContents();

	QApplication::restoreOverrideCursor();
}
"""

class PyDoshDialog(Ui_pyDosh, QtGui.QDialog):
	def __init__(self, parent=None):
		super(PyDoshDialog, self).__init__(parent=parent)

		import pdb
		pdb.set_trace()
