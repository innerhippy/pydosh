import math
from contextlib  import contextmanager
from PyQt4 import QtGui, QtCore, QtSql
from utils import showWaitCursor
from models import RecordModel, SortProxyModel
from helpBrowser import HelpBrowser
from csvDecoder import Decoder, DecoderException
from database import db
from ui_pydosh import Ui_pydosh
from dialogs import SettingsDialog, LoginDialog, TagDialog, ImportDialog
import enum
import pydosh_rc
import pdb


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

		self.tagEditButton.setEnabled(False)
		self.toggleCheckButton.setEnabled(False)
		self.deleteButton.setEnabled(False)

		self.checkedCombo.currentIndexChanged.connect(self.setFilter)
		self.inoutCombo.currentIndexChanged.connect(self.setFilter)
		self.typeCombo.currentIndexChanged.connect(self.setFilter)
		self.accountCombo.currentIndexChanged.connect(self.setFilter)
		self.descEdit.textChanged.connect(self.setFilter)
		self.amountEdit.textChanged.connect(self.setFilter)
		self.amountEdit.controlKeyPressed.connect(self.controlKeyPressed)
		self.tagEdit.editingFinished.connect(self.setFilter)
		self.startDateEdit.dateChanged.connect(self.setFilter)
		self.endDateEdit.dateChanged.connect(self.setFilter)
		self.toggleCheckButton.clicked.connect(self.toggleSelected)
		self.deleteButton.clicked.connect(self.deleteRecords)
		self.dateRangeCheckbox.stateChanged.connect(self.setEndDate)
		self.reloadButton.clicked.connect(self.reset)
		self.tableView.clicked.connect(self.itemChecked)
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
				self.typeCombo,
				self.dateRangeCheckbox,
				self.descEdit,
				self.amountEdit,
				self.startDateEdit,
				self.endDateEdit,
		)
		self.loadData()
		# TODO: remove!
		#self.addTagButtonPressed()
		#self.quit()

	def show(self):
		""" I'm sure there's a better way of doing this..
		need to call resizeColumnsToContents after show() so that the
		viewport height can be used to determine which rows to consider.
		Otherwise every row in the model will be used to calculate the
		column width (it seems) which is ugly.
		"""
		super(PydoshWindow, self).show()
		self.tableView.resizeColumnsToContents()


	def showHelp(self):

		browser = HelpBrowser(self)
		browser.showPage("main.html")

#	def showAbout(self):
#
#		QtGui.QMessageBox.about(self,
#			'About doshLogger',
#			"<html><p><h2>doshlogger</h2></p>"
#			"<p>version "
#			APPLICATION_VERSION
#			"</p>"
#			"<p>by Will Hall <a href=\"mailto:dev@innerhippy.com\">dev@innerhippy.com</a><br>"
#			"Copywrite (c) 2010. Will Hall </p>"
#			"<p>Written using Qt"
#			QT_VERSION_STR
#			"<br>"
##if defined(__GNUC__)
#			"Compiled using GCC"
#			__VERSION__
#			"<p>"
#			"<a href=\"http://www.innerhippy.com\">www.innerhippy.com</a></p>"
#			"enjoy!</html>"
##endif
#			));
#}


	@showWaitCursor
	def loadData(self):

		if not db.isConnected:
			return

		with self.blockAllSignals():

			self.model = None
			model = RecordModel(db.userId, self)

			model.setTable("records")
			model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
			model.select()

			proxyModel = SortProxyModel(self)
			proxyModel.setSourceModel(model)
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
			self.tableView.setColumnHidden(enum.kRecordColumn_User, True)
			self.tableView.setColumnHidden(enum.kRecordColumn_InsertDate, True)
			self.tableView.setSortingEnabled(True)
			self.tableView.sortByColumn(enum.kRecordColumn_Date, QtCore.Qt.DescendingOrder)
			self.tableView.horizontalHeader().setStretchLastSection(True)
			self.tableView.selectionModel().selectionChanged.connect(self.activateButtons)

			self.model = model
			self.reset()


	def setConnectionStatus(self, isConnected):
		if isConnected:
			self.connectionStatusText.setText('connected to %s@%s' % (db.database, db.hostname))
			self.connectionStatusIcon.setPixmap(QtGui.QPixmap(':/icons/thumb_up.png'))

		else:
			self.connectionStatusText.setText('not connected')
			self.connectionStatusIcon.setPixmap(QtGui.QPixmap(':/icons/thumb_down.png'))
			self.model = None

			self.tableView.setModel(None)
			self.displayRecordCount()


	def setEndDate(self, state):
		self.endDateEdit.setEnabled(state == QtCore.Qt.Checked)
		self.setFilter()

	def settingsDialog(self):
		dialog = SettingsDialog(self)
		dialog.exec_()
		self.setFilter()

	def loginDialog(self):
		dialog = LoginDialog(self)
		if dialog.exec_():
			self.loadData()

	def addTagButtonPressed(self):
		dialog = TagDialog(self.getSelectedRecordIds(), self)
		if dialog.exec_():
			self.setFilter()
			self.loadTags()

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
		creditField =  combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_CreditField).data()
		debitField =  combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_DebitField).data()
		currencySign =  combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_CurrencySign).data()
		dateFormat =  combo.model().index(combo.currentIndex(), enum.kAccountTypeColumn_DateFormat).data()

		# Save the settings for next time
		settings.setValue('options/importaccounttype', combo.currentText())
		settings.setValue('options/importdirectory', dialog.directory().absolutePath())

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
			self.reset()

	def itemChecked(self, index):

		if self.model is None:
			return

		if index.column() != enum.kRecordColumn_Checked:
			return

		proxyModel = self.tableView.model()
		recordId, ok = self.model.record(proxyModel.mapToSource(index).row()).value(enum.kRecordColumn_RecordId).toInt()
		if ok:
			self.toggleChecked([recordId])

	def activateButtons(self):

		model = self.tableView.selectionModel()
		enable = False

		if model:
			enable = len(model.selectedRows()) > 0

		self.tagEditButton.setEnabled(enable)
		self.toggleCheckButton.setEnabled(enable)
		self.deleteButton.setEnabled(enable)


	def controlKeyPressed(self, key):
		""" control key has been pressed - if we have a single row displayed, then toggle the status
		"""
		if self.model and self.model.rowCount() == 1:
			if key == QtCore.Qt.Key_Space:
				recordId, ok = self.model.record(0).value(enum.kRecordColumn_RecordId).toInt()
				if ok:
					self.toggleChecked([recordId])

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

		for index in selectionModel.selectedRows():
			dataModel.removeRow(proxyModel.mapToSource(index).row())

		dataModel.submitAll()

	def toggleChecked(self, recordIds):
		""" QStringList of record IDs to toggle
		"""
		if len(recordIds) == 0:
			return

		query = QtSql.QSqlQuery("""
			UPDATE records SET checked=abs(checked -1), checkdate='%(checkdate)s'
			WHERE recordid IN (%(recordids)s)
			""" % {
			'checkdate': QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
			'recordids': ','.join(str(rec) for rec in recordIds)
		})

		query.next()

		if query.lastError().isValid():
			QtGui.QMessageBox.critical(self, 'DB Error', query.lastError().text(), QtGui.QMessageBox.Ok)
			return

		visibleRow = self.tableView.indexAt(QtCore.QPoint(5,5))

		self.model.select()

		# Restore view position
		if visibleRow.isValid():
			self.tableView.scrollTo(visibleRow, QtGui.QAbstractItemView.PositionAtTop)

		if self.model.rowCount() == 0:
			# Smart focus - if we have no records showing then reset the last
			# search filter and set focus
			descFilter = self.descEdit.text()
			amountFilter = self.amountEdit.text()
			tagFilter = self.tagEdit.text()

			if descFilter and not amountFilter and not tagFilter:
				self.descEdit.clear()
				self.descEdit.setFocus(QtCore.Qt.OtherFocusReason)
			elif amountFilter and not descFilter and not tagFilter:
				self.amountEdit.clear()
				self.amountEdit.setFocus(QtCore.Qt.OtherFocusReason)
			elif tagFilter and not descFilter and not amountFilter:
				self.tagEdit.clear()
				self.tagEdit.setFocus(QtCore.Qt.OtherFocusReason)

		self.displayRecordCount()

	@contextmanager
	def blockAllSignals(self):
		try:
			for widget in self.__signalsToBlock:
				widget.blockSignals(True)
			yield
		finally:
			for widget in self.__signalsToBlock:
				widget.blockSignals(False)


	def populateAccounts(self):
		""" Extract account names from database and populate account combo
		"""
		self.accountCombo.clear()
		self.accountCombo.addItem('all')

		# Only pull in account types used by this user
		query = QtSql.QSqlQuery()
		query.prepare("""
			SELECT DISTINCT at.accountname, at.accounttypeid
			FROM accounttypes at
			INNER JOIN records r ON r.accounttypeid=at.accounttypeid
			WHERE r.userid=?
			ORDER BY at.accountname
		""")

		query.addBindValue(db.userId)
		query.exec_()

		while query.next():
			# Store the accounttypeid in the userData field
			self.accountCombo.addItem(query.value(0).toString(), query.value(1).toInt())

	def populateDates(self):

		query = QtSql.QSqlQuery('''
			SELECT MIN(date), MAX(date)
			FROM records
			WHERE userid=%d
		''' % db.userId)

		if query.next():
			startDate = query.value(0).toDate()
			endDate = query.value(1).toDate()
			print 'min %r, max %r' % (startDate, endDate)

			self.startDateEdit.setDateRange(startDate, endDate)
			self.endDateEdit.setDateRange(startDate, endDate)

			self.endDateEdit.setDate(self.startDateEdit.maximumDate())
			self.startDateEdit.setDate(self.endDateEdit.date().addYears(-1))

			print 'set: start %r, end %r' % (self.startDateEdit.date(), self.endDateEdit.date())

	def loadTags(self):
		tagList = []
		query = QtSql.QSqlQuery(
				"SELECT tagname FROM tags WHERE userid=%d" % db.userId
		)

		while query.next():
			tagList.append(query.value(0).toString())

		completer = QtGui.QCompleter(tagList, self.tagEdit)
		self.tagEdit.setCompleter(completer)
		self.tagEdit.completer().setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.tagEdit.completer().setCompletionMode(QtGui.QCompleter.PopupCompletion)

		completer.activated.connect(self.setFilter)


	def getSelectedRecordIds(self):

		# Get recordids from all selected rows
		selectionModel = self.tableView.selectionModel()
		if selectionModel is None:
			return []

		proxyModel = self.tableView.model()

		recordIds = []
		for index in selectionModel.selectedRows():
			recordId, ok = self.model.record(proxyModel.mapToSource(index).row()).value(enum.kRecordColumn_RecordId).toInt()
			if ok:
				recordIds.append(recordId)


		return recordIds


	def toggleSelected(self):
		self.toggleChecked(self.getSelectedRecordIds())

	def reset(self):

		if self.model is None or not db.isConnected:
			return

		with self.blockAllSignals():
			self.populateAccounts()
			self.populateDates()
			self.loadTags()
			self.checkedCombo.setCurrentIndex(0)
			self.typeCombo.setCurrentIndex(0)
			self.accountCombo.setCurrentIndex(0)

			self.inoutCombo.setCurrentIndex(0)
			self.amountEdit.clear()
			self.descEdit.clear()
			self.tagEdit.clear()
			self.dateRangeCheckbox.setCheckState(QtCore.Qt.Checked)
			self.endDateEdit.setEnabled(True)
			self.tableView.sortByColumn(enum.kRecordColumn_Date, QtCore.Qt.DescendingOrder)

		self.setFilter()

	def addActions(self):
		quitAction = QtGui.QAction('&Quit', self)
		quitAction.setShortcut('Alt+q')
		quitAction.setStatusTip('Exit the program')
		quitAction.setIcon(QtGui.QIcon(':/icons/exit.png'))
		quitAction.triggered.connect(self.close)

		settingsAction = QtGui.QAction('&Settings', self)
		settingsAction.setShortcut('Alt+s')
		settingsAction.setStatusTip('Change the settings')
		settingsAction.setIcon(QtGui.QIcon(':/icons/wrench.png'))
		settingsAction.triggered.connect(self.settingsDialog)

		loginAction = QtGui.QAction('&Login', self)
		loginAction.setShortcut('Alt+l')
		loginAction.setStatusTip('Login')
		loginAction.setIcon(QtGui.QIcon(':/icons/disconnect.png'))
		loginAction.triggered.connect(self.loginDialog)

		importAction = QtGui.QAction('&Import', self)
		importAction.setShortcut('Alt+i')
		importAction.setStatusTip('Import Bank statements')
		importAction.setIcon(QtGui.QIcon(':/icons/import.png'))
		importAction.triggered.connect(self.importDialog)

		aboutAction = QtGui.QAction('&About', self)
		aboutAction.setStatusTip('About')
		aboutAction.setIcon(QtGui.QIcon(':/icons/help.png'))
#		aboutAction.triggered.connect(self.showAbout)

		helpAction = QtGui.QAction('&Help', self)
		helpAction.setStatusTip('Help')
		helpAction.setIcon(QtGui.QIcon(':/icons/help.png'))
		helpAction.triggered.connect(self.showHelp)

		self.addAction(settingsAction)
		self.addAction(importAction)
		self.addAction(quitAction)
		self.addAction(aboutAction)
		self.addAction(helpAction)
		self.addAction(loginAction)

		# File menu
		fileMenu = self.menuBar().addMenu('&Tools')
		fileMenu.addAction(loginAction)
		fileMenu.addAction(settingsAction)
		fileMenu.addAction(importAction)
		fileMenu.addAction(quitAction)

		# Help menu
		helpMenu = self.menuBar().addMenu('&Help')
		helpMenu.addAction(aboutAction)
		helpMenu.addAction(helpAction)


	def displayRecordCount(self):
		numRecords = 0
		totalRecords = 0
		inTotal = 0.0
		outTotal = 0.0

		if self.model is not None:
			numRecords = self.model.rowCount()

			query = QtSql.QSqlQuery('SELECT COUNT(*) FROM records WHERE userid=%d' % db.userId)
			query.next()
			totalRecords, _ = query.value(0).toInt()

			for i in xrange(numRecords):
				amount, _ = self.model.record(i).value(enum.kRecordColumn_Amount).toDouble()
				if amount > 0.0:
					inTotal += amount
				else:
					outTotal += math.fabs(amount)

		self.inTotalLabel.setText(QtCore.QString("%L1").arg(inTotal, 0, 'f', 2))
		self.outTotalLabel.setText(QtCore.QString("%L1").arg(outTotal, 0, 'f', 2))
		self.recordCountLabel.setText('%d / %d' % (numRecords, totalRecords))

	@showWaitCursor
	def setFilter(self, *args):

		if self.model is None or not db.isConnected:
			return

		queryFilter = []

		# Account filter
		accountNo = self.accountCombo.itemData(self.accountCombo.currentIndex(), QtCore.Qt.UserRole)
		if accountNo.isValid():
			queryFilter.append('r.accounttypeid=%d' % accountNo.toInt())

		# Date filter
		startDate = self.startDateEdit.date()
		if self.dateRangeCheckbox.checkState() == QtCore.Qt.Unchecked:
			endDate = self.endDateEdit.date()
		else:
			endDate = startDate

		if startDate.isValid() and endDate.isValid():
			queryFilter.append("date >= '%s'" % startDate.toString(QtCore.Qt.ISODate))
			queryFilter.append("date < '%s'" % endDate.addMonths(1).toString(QtCore.Qt.ISODate))
			print 'query:', queryFilter[-2]
			print 'query:', queryFilter[-1]

		# checked state filter
		state, ok = self.checkedCombo.itemData(self.checkedCombo.currentIndex(), QtCore.Qt.UserRole).toInt()
		if ok:
			if state == enum.kCheckedStatus_Checked:
				queryFilter.append('checked=1')
			elif state == enum.kCheckedStatus_UnChecked:
				queryFilter.append('checked=0')

		# money in/out filter
		state, ok = self.inoutCombo.itemData(self.inoutCombo.currentIndex(), QtCore.Qt.UserRole).toInt()
		if ok:
			if state == enum.kInOutStatus_In:
				queryFilter.append('amount > 0')
			elif state == enum.kInOutStatus_Out:
				queryFilter.append('amount < 0')

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
					queryFilter.append('abs(amount) %s %s' % (rx.cap(1), rx.cap(2)))
				else:
					# Input not complete yet.
					return
			else:
				# No operator supplied - treat amount as a string
				queryFilter.append(
					"CAST(r.amount AS char(10)) LIKE '%s%%' OR CAST(r.amount AS char(10)) LIKE '-%s%%'" % 
					(amountFilter, amountFilter))

		# tag filter
		if self.tagEdit.text():
			queryFilter.append("""
				r.recordid IN 
				(SELECT recordid from recordtags rt 
					JOIN tags t ON t.tagid=rt.tagid 
					WHERE t.tagname ='%s'
				)
			""" % self.tagEdit.text())

		self.model.setFilter('\nAND '.join(queryFilter))

		print self.model.query().lastQuery().replace(' AND ', '').replace('\n', ' ')
		self.tableView.resizeColumnsToContents()
		self.displayRecordCount()

