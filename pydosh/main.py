from contextlib  import contextmanager
from version import __VERSION__
from PyQt4 import QtGui, QtCore, QtSql
from utils import showWaitCursorDecorator, showWaitCursor
from models import RecordModel, SortProxyModel, CheckComboModel
from csvdecoder import Decoder, DecoderException
from database import db
from ui_pydosh import Ui_pydosh
from dialogs import SettingsDialog, TagDialog, ImportDialog
import enum
import pydosh_rc


class PydoshWindow(Ui_pydosh, QtGui.QMainWindow):
	def __init__(self, parent=None):
		super(PydoshWindow, self).__init__(parent=parent)
		self.setupUi(self)
		self.model = None

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

		self.checkedCombo.addItem('all', enum.kCheckedStatus_All)
		self.checkedCombo.addItem('checked', enum.kCheckedStatus_Checked)
		self.checkedCombo.addItem('unchecked', enum.kCheckedStatus_UnChecked)

		self.inoutCombo.addItem('all', enum.kInOutStatus_All)
		self.inoutCombo.addItem('in', enum.kInOutStatus_In)
		self.inoutCombo.addItem('out', enum.kInOutStatus_Out)

		self.dateCombo.addItem('All', userData=enum.kDate_All)
		self.dateCombo.addItem('Last 12 months', userData=enum.kDate_PreviousYear)
		self.dateCombo.addItem('Last month', userData=enum.kDate_PreviousMonth)
		self.dateCombo.addItem('Last import', userData=enum.kdate_LastImport)

		self.toggleCheckButton.setEnabled(False)
		self.deleteButton.setEnabled(False)

		self.accountCombo.setDefaultText('all')
		self.tagCombo.selectionChanged.connect(self.setFilter)
		self.checkedCombo.currentIndexChanged.connect(self.setFilter)
		self.inoutCombo.currentIndexChanged.connect(self.setFilter)
		self.accountCombo.selectionChanged.connect(self.setFilter)
		self.tagCombo.selectionChanged.connect(self.setFilter)
		self.descEdit.textChanged.connect(self.setFilter)
		self.amountEdit.textChanged.connect(self.setFilter)
		self.amountEdit.controlKeyPressed.connect(self.controlKeyPressed)
		self.startDateEdit.dateChanged.connect(self.setFilter)
		self.endDateEdit.dateChanged.connect(self.setFilter)
		self.toggleCheckButton.clicked.connect(self.toggleSelected)
		self.deleteButton.clicked.connect(self.deleteRecords)
		self.dateCombo.currentIndexChanged.connect(self.setDate)
		self.startDateEdit.dateChanged.connect(self.setFilter)
		self.endDateEdit.dateChanged.connect(self.setFilter)
		self.reloadButton.clicked.connect(self.reset)
		self.tagEditButton.pressed.connect(self.addTagButtonPressed)

		db.connected.connect(self.setConnectionStatus)

		amountValidator = QtGui.QRegExpValidator(QtCore.QRegExp("[<>=0-9.]*"), self)
		self.amountEdit.setValidator(amountValidator)

		self.startDateEdit.setCalendarPopup(True)
		self.endDateEdit.setCalendarPopup(True)

		self.addActions()

		self.inTotalLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
		self.outTotalLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
		self.recordCountLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)

		self.setConnectionStatus(db.isConnected)

		self.__signalsToBlock = (
				self.accountCombo,
				self.checkedCombo,
				self.inoutCombo,
				self.tagCombo,
				self.dateCombo,
				self.descEdit,
				self.amountEdit,
				self.startDateEdit,
				self.endDateEdit,
		)

		with self.blockAllSignals():

			self.model = None
			recordsModel = RecordModel(db.userId, self)
			recordsModel.setTable("records")
			recordsModel.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
			recordsModel.select()
			self.model = recordsModel

			proxyModel = SortProxyModel(self)
			proxyModel.setSourceModel(recordsModel)
			proxyModel.setFilterKeyColumn(-1)

			self.tableView.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | QtGui.QAbstractItemView.SelectedClicked)
			self.tableView.setModel(proxyModel)
			self.tableView.verticalHeader().hide()
			self.tableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
			self.tableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
			self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

			self.tableView.setColumnHidden(enum.kRecordColumn_RecordId, True)
			self.tableView.setColumnHidden(enum.kRecordColumn_CheckDate, True)
			self.tableView.setColumnHidden(enum.kRecordColumn_RawData, True)
			self.tableView.setColumnHidden(enum.kRecordColumn_InsertDate, True)
			self.tableView.setSortingEnabled(True)
			self.tableView.sortByColumn(enum.kRecordColumn_Date, QtCore.Qt.DescendingOrder)
			self.tableView.horizontalHeader().setStretchLastSection(True)
			self.tableView.selectionModel().selectionChanged.connect(self.activateButtons)

			# Set sql data model for account types
			self.accountCombo.clear()
	
			accountModel = CheckComboModel()
			accountModel.setTable('accounttypes')
			accountModel.setFilter("""
				accounttypeid IN (
					SELECT distinct accounttypeid
					FROM records
					WHERE userid=%d)
				""" % db.userId)

			accountModel.select()
			accountModel.setUserRoleColumn(enum.kAccountTypeColumn_AccountTypeId)
			self.accountCombo.setModelColumn(enum.kAccountTypeColumn_AccountName)
			self.accountCombo.setModel(accountModel)

			# Set tag model
			tagModel = CheckComboModel()
			tagModel.setTable('tags')
	
			# Only display tags that have been set on the current records
			tagModel.setFilter("""
				userid=%d
				AND tagid IN (
					SELECT DISTINCT tagid
					FROM recordtags rt
					INNER JOIN records r
					ON r.recordid=rt.recordid
					)
				""" % db.userId)
			tagModel.select()
			tagModel.setUserRoleColumn(enum.kTagsColumn_TagId)
			self.tagCombo.setModelColumn(enum.kTagsColumn_TagName)
			self.tagCombo.setModel(tagModel)

			self.reset()

	def showAbout(self):

		QtGui.QMessageBox.about(self,
			'About pydosh',
			"<html><p><h2>pydosh</h2></p>"
			"<p>version %s</p>"
			"<p>by Will Hall <a href=\"mailto:will@innerhippy.com\">will@innerhippy.com</a></p>"
			"<p>Copywrite (c) 2013.</p>"
			"<p>Written using PyQt %s</p>"
			"<p><a href=\"http://www.innerhippy.com\">www.innerhippy.com</a></p>"
			"enjoy!</html>" % (__VERSION__, QtCore.QT_VERSION_STR)
			)

	def setConnectionStatus(self, isConnected):
		if isConnected:
			self.connectionStatusText.setText('connected to %s@%s' % (db.database, db.hostname))

		else:
			self.connectionStatusText.setText('not connected')
			self.model = None

			self.tableView.setModel(None)
			self.displayRecordCount()

	def setDate(self):
		selected = self.dateCombo.itemData(self.dateCombo.currentIndex(), QtCore.Qt.UserRole).toPyObject()

		if selected == enum.kDate_All:
			self.startDateEdit.setDate(self.startDateEdit.minimumDate())
			self.endDateEdit.setDate(self.endDateEdit.maximumDate())
			self.startDateEdit.setEnabled(True)
			self.endDateEdit.setEnabled(True)
		elif selected == enum.kDate_PreviousMonth:
			self.startDateEdit.setDate(self.endDateEdit.date().addMonths(-1))
			self.endDateEdit.setEnabled(True)
			self.startDateEdit.setEnabled(False)
		elif selected == enum.kDate_PreviousYear:
			self.startDateEdit.setDate(self.endDateEdit.date().addYears(-1))
			self.startDateEdit.setEnabled(True)
			self.endDateEdit.setEnabled(True)
		elif selected == enum.kdate_LastImport:
			self.startDateEdit.setEnabled(False)
			self.endDateEdit.setEnabled(False)
			self.setFilter()

	def settingsDialog(self):
		dialog = SettingsDialog(self)
		dialog.exec_()
		self.setFilter()

	def addTagButtonPressed(self):
		# Get recordids from all selected rows
		selectionModel = self.tableView.selectionModel()
		if selectionModel is None:
			return []

		proxyModel = self.tableView.model()
		recordIds = []
		for proxyIndex in selectionModel.selectedRows():
			index = self.model.index(proxyModel.mapToSource(proxyIndex).row(), enum.kRecordColumn_RecordId) 
			recordIds.append(index.data().toPyObject())

		dialog = TagDialog(recordIds, self)
		if dialog.exec_():
			self.tagCombo.model().select()

	def importDialog(self):
		if not db.isConnected:
			return

		combo = QtGui.QComboBox(self)
		model = QtSql.QSqlTableModel(self)
		model.setTable('accounttypes')
		model.select()
		combo.setModel(model)
		combo.setModelColumn(enum.kAccountTypeColumn_AccountName)

		# find the previous accounttype that was used (if any)
		settings = QtCore.QSettings()
		accounttype = settings.value("options/importaccounttype").toString()

		index = combo.findText(accounttype)

		if index != -1:
			combo.setCurrentIndex(index)
		else:
			combo.setCurrentIndex(0)

		label = QtGui.QLabel('Account type:')
		importDir = settings.value("options/importdirectory").toString()

		if importDir.isEmpty():
			importDir = QtCore.QDir.homePath()

		dialog = QtGui.QFileDialog(self, 'Open File', importDir, "*.csv")
		dialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
		dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog)

		gridbox = dialog.layout()

		if gridbox:
			gridbox.addWidget(label)
			gridbox.addWidget(combo)

		if not dialog.exec_():
			return

		accountId, ok = combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_AccountTypeId).data().toInt()
		if not ok:
			QtGui.QMessageBox.critical(self, 'Import Error', 'No account type specified', QtGui.QMessageBox.Ok)
			return

		fileNames = QtCore.QStringList([QtCore.QFileInfo(f).fileName() for f in dialog.selectedFiles()]) 
		dateField = combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_DateField).data()
		descriptionField = combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_DescriptionField).data()
		creditField = combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_CreditField).data()
		debitField = combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_DebitField).data()
		currencySign = combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_CurrencySign).data()
		dateFormat = combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_DateFormat).data()

		# Save the settings for next time
		settings.setValue('options/importaccounttype', combo.currentText())
		settings.setValue('options/importdirectory', dialog.directory().absolutePath())

		with showWaitCursor():
			try:
				decoder = Decoder(
						dateField,
						descriptionField,
						creditField,
						debitField,
						currencySign,
						dateFormat,
						dialog.selectedFiles())
			except DecoderException, exc:
				QtGui.QMessageBox.critical(self, 'Import Error', str(exc), QtGui.QMessageBox.Ok)
				return

			dialog = ImportDialog(decoder.records, accountId, self)
			dialog.setWindowTitle(fileNames.join(', '))

		if dialog.exec_():
			self.accountCombo.model().select()
			self.reset()

	def activateButtons(self):

		model = self.tableView.selectionModel()
		enable = False

		if model:
			enable = len(model.selectedRows()) > 0

		self.toggleCheckButton.setEnabled(enable)
		self.deleteButton.setEnabled(enable)


	def controlKeyPressed(self, key):
		""" control key has been pressed - if we have a single row displayed, then toggle the status
		"""
		if self.model and key == QtCore.Qt.Key_Space and self.model.rowCount() == 1:
			self.tableView.selectAll()
			self.toggleSelected()

	def deleteRecords(self):
		""" Delete selected records
		"""
		selectionModel = self.tableView.selectionModel()
		proxyModel = self.tableView.model()
		dataModel = proxyModel.sourceModel()

		if QtGui.QMessageBox.question(
				self, 'Delete Records',
				'Are you sure you want to delete %d rows?' % len(selectionModel.selectedRows()), 
				QtGui.QMessageBox.Yes|QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
			return

		with showWaitCursor():
			for index in selectionModel.selectedRows():
				dataModel.removeRow(proxyModel.mapToSource(index).row())
	
			dataModel.submitAll()
			self.accountCombo.model().select()
			self.tagCombo.model().select()

	@contextmanager
	def blockAllSignals(self):
		try:
			for widget in self.__signalsToBlock:
				widget.blockSignals(True)
			yield
		finally:
			for widget in self.__signalsToBlock:
				widget.blockSignals(False)


	def populateDates(self):
		query = QtSql.QSqlQuery("""
				SELECT MIN(date), MAX(date)
				FROM records
				WHERE userid=%d
			""" % db.userId)

		if query.next():
			startDate = query.value(0).toDate()
			endDate = query.value(1).toDate()

			self.startDateEdit.setDateRange(startDate, endDate)
			self.endDateEdit.setDateRange(startDate, endDate)

			self.startDateEdit.setDate(startDate)
			self.endDateEdit.setDate(endDate)

	@showWaitCursorDecorator
	def toggleSelected(self, *args):

		selectionModel = self.tableView.selectionModel()

		if selectionModel is None:
			return

		proxyModel = self.tableView.model()

		for proxyIndex in selectionModel.selectedRows():
			index = self.model.index(proxyModel.mapToSource(proxyIndex).row(), enum.kRecordColumn_Checked) 
			checkState = index.data(QtCore.Qt.CheckStateRole).toPyObject()
			newState = QtCore.Qt.Unchecked if checkState == QtCore.Qt.Checked else QtCore.Qt.Checked
			self.model.setData(index, QtCore.QVariant(newState), QtCore.Qt.CheckStateRole)

		self.displayRecordCount()

	def reset(self):
		if self.model is None or not db.isConnected:
			return

		with self.blockAllSignals():
			self.populateDates()
			self.checkedCombo.setCurrentIndex(enum.kCheckedStatus_All)
			self.dateCombo.setCurrentIndex(enum.kDate_PreviousYear)
			self.setDate()
			self.tagCombo.clearAll()
			self.accountCombo.clearAll()
			self.inoutCombo.setCurrentIndex(enum.kInOutStatus_All)
			self.amountEdit.clear()
			self.descEdit.clear()
			self.endDateEdit.setEnabled(True)
			self.tableView.sortByColumn(enum.kRecordColumn_Date, QtCore.Qt.DescendingOrder)

		self.setFilter()

	def addActions(self):
		quitAction = QtGui.QAction(QtGui.QIcon(':/icons/exit.png'), '&Quit', self)
		quitAction.setShortcut('Alt+q')
		quitAction.setStatusTip('Exit the program')
		quitAction.triggered.connect(self.close)

		settingsAction = QtGui.QAction(QtGui.QIcon(':/icons/wrench.png'), '&Settings', self)
		settingsAction.setShortcut('Alt+s')
		settingsAction.setStatusTip('Change the settings')
		settingsAction.triggered.connect(self.settingsDialog)

		importAction = QtGui.QAction(QtGui.QIcon(':/icons/import.png'), '&Import', self)
		importAction.setShortcut('Alt+i')
		importAction.setStatusTip('Import Bank statements')
		importAction.triggered.connect(self.importDialog)

		aboutAction = QtGui.QAction(QtGui.QIcon(':/icons/help.png'), '&About', self)
		aboutAction.setStatusTip('About')
		aboutAction.triggered.connect(self.showAbout)

		self.addAction(settingsAction)
		self.addAction(importAction)
		self.addAction(quitAction)
		self.addAction(aboutAction)

		# File menu
		fileMenu = self.menuBar().addMenu('&Tools')
		fileMenu.addAction(settingsAction)
		fileMenu.addAction(importAction)
		fileMenu.addAction(quitAction)

		helpMenu = self.menuBar().addMenu('&Help')
		helpMenu.addAction(aboutAction)


	def displayRecordCount(self):
		numRecords = 0
		totalRecords = 0
		inTotal = 0.0
		outTotal = 0.0

		if self.model is not None:
			numRecords = self.model.rowCount()

			query = QtSql.QSqlQuery('SELECT COUNT(*) FROM records WHERE userid=%d' % db.userId)
			query.next()
			totalRecords = query.value(0).toPyObject()

			for i in xrange(numRecords):
				amount, _ = self.model.record(i).value(enum.kRecordColumn_Amount).toDouble()
				if amount > 0.0:
					inTotal += amount
				else:
					outTotal += abs(amount)

		self.inTotalLabel.setText(QtCore.QString("%L1").arg(inTotal, 0, 'f', 2))
		self.outTotalLabel.setText(QtCore.QString("%L1").arg(outTotal, 0, 'f', 2))
		self.recordCountLabel.setText('%d / %d' % (numRecords, totalRecords))

	@showWaitCursorDecorator
	def setFilter(self, *args):
		if self.model is None or not db.isConnected:
			return

		queryFilter = []

		# Account filter
		accountIds = [index.data(QtCore.Qt.UserRole).toPyObject() for index in self.accountCombo.checkedIndexes()]
		if accountIds:
			queryFilter.append('r.accounttypeid in (%s)' % ', '.join(str(acid) for acid in accountIds))

		# Date filter
		if self.dateCombo.currentIndex() == enum.kdate_LastImport:
			queryFilter.append("""
				r.insertdate = (
					SELECT MAX(insertdate) 
					FROM records)
			""")
		else:
			startDate = self.startDateEdit.date()
			endDate = self.endDateEdit.date()
	
			if startDate.isValid() and endDate.isValid():
				queryFilter.append("r.date >= '%s'" % startDate.toString(QtCore.Qt.ISODate))
				queryFilter.append("r.date <= '%s'" % endDate.toString(QtCore.Qt.ISODate))

		# checked state filter
		state, ok = self.checkedCombo.itemData(self.checkedCombo.currentIndex(), QtCore.Qt.UserRole).toInt()
		if ok:
			if state == enum.kCheckedStatus_Checked:
				queryFilter.append('r.checked=1')
			elif state == enum.kCheckedStatus_UnChecked:
				queryFilter.append('r.checked=0')

		# money in/out filter
		state, ok = self.inoutCombo.itemData(self.inoutCombo.currentIndex(), QtCore.Qt.UserRole).toInt()
		if ok:
			if state == enum.kInOutStatus_In:
				queryFilter.append('r.amount > 0')
			elif state == enum.kInOutStatus_Out:
				queryFilter.append('r.amount < 0')

		# description filter
		if self.descEdit.text():
			queryFilter.append("lower(r.description) LIKE '%%%s%%'" % self.descEdit.text().toLower())

		# amount filter. May contain operators < > <= or >=
		amountFilter = self.amountEdit.text()
		if amountFilter:
			if amountFilter.contains(QtCore.QRegExp('[<>=]+')):
				# looks like we have operators, test validity and amount
				rx = QtCore.QRegExp('^(=|>|<|>=|<=)([\\.\\d+]+)')
				if rx.indexIn(amountFilter) != -1:
					queryFilter.append('abs(r.amount) %s %s' % (rx.cap(1), rx.cap(2)))
				else:
					# Input not complete yet.
					return
			else:
				# No operator supplied - treat amount as a string
				queryFilter.append(
					"CAST(r.amount AS char(10)) LIKE '%s%%' OR CAST(r.amount AS char(10)) LIKE '-%s%%'" %
					(amountFilter, amountFilter))

		# tag filter
		tagIds = [index.data(QtCore.Qt.UserRole).toPyObject() for index in self.tagCombo.checkedIndexes()]

		if tagIds:
			queryFilter.append("""
				r.recordid IN (
					SELECT recordid
					FROM recordtags
					WHERE tagid in (%s))
				""" % ', '.join([str(tagid) for tagid in tagIds]))

		self.model.setFilter('\nAND '.join(queryFilter))
		#print self.model.query().lastQuery().replace(' AND ', '').replace('\n', ' ')

		self.tableView.resizeColumnsToContents()
		self.displayRecordCount()

