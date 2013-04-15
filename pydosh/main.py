from contextlib  import contextmanager
import operator
from PyQt4 import QtGui, QtCore, QtSql
from version import __VERSION__
import utils
from models import RecordModel, SortProxyModel, CheckComboModel, TagModel
from csvdecoder import Decoder, DecoderException
from database import db
from ui_pydosh import Ui_pydosh
from dialogs import SettingsDialog, ImportDialog
import enum
import pydosh_rc

class PydoshWindow(Ui_pydosh, QtGui.QMainWindow):
	def __init__(self, parent=None):
		super(PydoshWindow, self).__init__(parent=parent)
		self.setupUi(self)

		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

		self.checkedCombo.addItem('all', enum.kCheckedStatus_All)
		self.checkedCombo.addItem('checked', enum.kCheckedStatus_Checked)
		self.checkedCombo.addItem('unchecked', enum.kCheckedStatus_UnChecked)

		self.inoutCombo.addItem('all', enum.kInOutStatus_All)
		self.inoutCombo.addItem('in', enum.kInOutStatus_In)
		self.inoutCombo.addItem('out', enum.kInOutStatus_Out)

		self.tagsCombo.addItem('all', enum.kTagCombo_All)
		self.tagsCombo.addItem('with tags', enum.kTagCombo_With)
		self.tagsCombo.addItem('without tags', enum.kTagCombo_Without)

		self.dateCombo.addItem('All', userData=enum.kDate_All)
		self.dateCombo.addItem('Last 12 months', userData=enum.kDate_PreviousYear)
		self.dateCombo.addItem('Last month', userData=enum.kDate_PreviousMonth)
		self.dateCombo.addItem('Last import', userData=enum.kdate_LastImport)

		self.toggleCheckButton.setEnabled(False)
		self.deleteButton.setEnabled(False)
		self.removeTagButton.setEnabled(False)

		self.accountCombo.setDefaultText('all')
#		self.accountCombo.selectionChanged.connect(self.setFilter)
		#self.checkedCombo.currentIndexChanged.connect(self.setFilter)
		#self.tagsCombo.currentIndexChanged.connect(self.setFilter)
		#self.inoutCombo.currentIndexChanged.connect(self.setFilter)
		#self.descEdit.textChanged.connect(self.setFilter)
		self.scrolltoEdit.textChanged.connect(self.scrollTo)
		#self.amountEdit.textChanged.connect(self.setFilter)
		self.amountEdit.controlKeyPressed.connect(self.controlKeyPressed)
		self.toggleCheckButton.clicked.connect(self.toggleSelected)
		self.deleteButton.clicked.connect(self.deleteRecords)
		self.dateCombo.currentIndexChanged.connect(self.dateRangeSelected)
#		self.startDateEdit.dateChanged.connect(self.setFilter)
#		self.endDateEdit.dateChanged.connect(self.setFilter)
		self.reloadButton.clicked.connect(self.reset)
		self.addTagButton.clicked.connect(self.addTag)
		self.removeTagButton.clicked.connect(self.removeTag)

		self.connectionStatusText.setText('connected to %s@%s' % (db.database, db.hostname))

		amountValidator = QtGui.QRegExpValidator(QtCore.QRegExp("[<>=0-9.]*"), self)
		self.amountEdit.setValidator(amountValidator)

		self.startDateEdit.setCalendarPopup(True)
		self.endDateEdit.setCalendarPopup(True)

		self.addActions()

		self.inTotalLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
		self.outTotalLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
		self.recordCountLabel.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)

		self.__signalsToBlock = (
				self.accountCombo,
				self.checkedCombo,
				self.tagsCombo,
				self.inoutCombo,
				self.descEdit,
				self.scrolltoEdit,
				self.amountEdit,
				self.dateCombo,
				self.startDateEdit,
				self.endDateEdit,
		)

#		self.filterTagIds = set()
		self.maxInsertDate = None

		with utils.blockSignals(*self.__signalsToBlock):

			model = RecordModel(self)
			model.setTable('records')
			model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
			model.dataChanged.connect(self.recordsChanged)
			model.select()

			proxyModel = SortProxyModel(self)
			proxyModel.setDynamicSortFilter(True)

			self.startDateEdit.dateChanged.connect(proxyModel.setStartDate)
			self.endDateEdit.dateChanged.connect(proxyModel.setEndDate)
			self.accountCombo.selectionChanged.connect(self.accountSelectionChanged)
			self.tagsCombo.currentIndexChanged.connect(self.tagSelectionChanged)
			self.checkedCombo.currentIndexChanged.connect(self.checkedSelectionChanged)
			self.inoutCombo.currentIndexChanged.connect(self.inOutSelectionChanged)
			self.descEdit.textChanged.connect(proxyModel.setDescriptionFilter)
			self.amountEdit.textChanged.connect(self.amountFilterChanged)
			
			proxyModel.filterChanged.connect(self.recordsChanged)
			proxyModel.setSourceModel(model)
			proxyModel.sort(enum.kRecordColumn_Date, QtCore.Qt.AscendingOrder)

			self.tableView.setModel(proxyModel)
			self.tableView.verticalHeader().hide()
			self.tableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
			self.tableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
			self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

			self.tableView.setColumnHidden(enum.kRecordColumn_RecordId, True)
			self.tableView.setColumnHidden(enum.kRecordColumn_AccountTypeId, True)
			self.tableView.setColumnHidden(enum.kRecordColumn_CheckDate, True)
			self.tableView.setColumnHidden(enum.kRecordColumn_RawData, True)
			self.tableView.setColumnHidden(enum.kRecordColumn_InsertDate, True)
			self.tableView.setSortingEnabled(True)

			self.tableView.horizontalHeader().setResizeMode(enum.kRecordColumn_Description, QtGui.QHeaderView.Stretch)
			self.tableView.selectionModel().selectionChanged.connect(self.recordSelectionChanged)

			self.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
			self.tableView.customContextMenuRequested.connect(self.tagEditPopup)

			model = TagModel(self)
			model.tagsChanged.connect(self.tagModelChanged)
			model.selectionChanged.connect(self.tableView.model().setTagFilter)
#			model.selectionChanged.connect(self.setTagFilter)
			proxyModel = QtGui.QSortFilterProxyModel(self)
			proxyModel.setSourceModel(model)
			proxyModel.sort(enum.kTagsColumn_Amount_out, QtCore.Qt.AscendingOrder)

			self.tagView.setModel(proxyModel)
			self.tagView.setColumnHidden(enum.kTagsColumn_TagId, True)
			self.tagView.setColumnHidden(enum.kTagsColumn_RecordIds, True)
			self.tagView.setSortingEnabled(True)
			self.tagView.sortByColumn(enum.kTagsColumn_TagName, QtCore.Qt.AscendingOrder)
			self.tagView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
			self.tagView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
			self.tagView.selectionModel().selectionChanged.connect(self.enableRemoveTagButton)

			self.tagView.verticalHeader().hide()
			self.tagView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
			self.tagView.setStyleSheet('QTableView {background-color: transparent;}')
			self.tagView.setShowGrid(False)

			# Set sql data model for account types
			# TODO: fixme
			self.accountCombo.clear()

			accountModel = CheckComboModel(self)
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
#
#			from signaltracer import SignalTracer
#			tracer=SignalTracer()
#			tracer.monitor(self.tableView.model(), self.tableView.model().sourceModel())

		self.reset()

	def accountSelectionChanged(self):
		""" Tell the proxy filter to filter on selected account ids
		"""
		accountIds = [index.data(QtCore.Qt.UserRole).toPyObject() for index in self.accountCombo.checkedIndexes()]
		self.tableView.model().setAccountFilter(accountIds)


	def tagSelectionChanged(self, index):
		""" Basic tag filter (has tags or not)
		"""
		state = self.tagsCombo.itemData(index, QtCore.Qt.UserRole).toPyObject()
		if state == enum.kTagCombo_With:
			value = True
		elif state == enum.kTagCombo_Without:
			value = False
		else:
			value = None
		self.tableView.model().setHasTagsFilter(value)

	def checkedSelectionChanged(self, index):
		""" Set filter for checked records
		"""
		state = self.checkedCombo.itemData(index, QtCore.Qt.UserRole).toPyObject()
		if state == enum.kCheckedStatus_Checked:
			value = True
		elif state == enum.kCheckedStatus_UnChecked:
			value = False
		else:
			value = None
		self.tableView.model().setCheckedFilter(value)

	def inOutSelectionChanged(self, index):
		""" Set filter for in/out amount
		"""
		state = self.inoutCombo.itemData(index, QtCore.Qt.UserRole).toPyObject()
		if state == enum.kInOutStatus_In:
			value = True
		elif state == enum.kInOutStatus_Out:
			value = False
		else:
			value = None
		self.tableView.model().setCreditFilter(value)

	def amountFilterChanged(self, text):
		if text:
			if text.contains(QtCore.QRegExp('[<>=]+')):
				# looks like we have operators, test validity and amount
				operatorMap = {
					'=':  operator.eq,
					'>':  operator.gt,
					'<':  operator.lt,
					'>=': operator.ge,
					'<=': operator.le
				}
				rx = QtCore.QRegExp('^(=|>|<|>=|<=)([\\.\\d+]+)')
				if rx.indexIn(text) != -1 and str(rx.cap(1)) in operatorMap:
					self.tableView.model().setAmountFilter(rx.cap(2), operatorMap[str(rx.cap(1))])
				else:
					# Input not complete yet.
					return
			else:
				# No operator supplied - treat amount as a string
				self.tableView.model().setAmountFilter(text)
		else:
			# No filter
			self.tableView.model().setAmountFilter(None)

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

	def selectDateRange(self):
		selected = self.dateCombo.itemData(self.dateCombo.currentIndex(), QtCore.Qt.UserRole).toPyObject()

		# Clear the filters but don't trigger a re-draw just yet
		with utils.blockSignals(self.tableView.model()):
			self.tableView.model().setStartDate(None)
			self.tableView.model().setEndDate(None)
			self.tableView.model().setInsertDate(None)

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
			self.tableView.model().setInsertDate(self.maxInsertDate)
			self.startDateEdit.setEnabled(False)
			self.endDateEdit.setEnabled(False)

	def settingsDialog(self):
		""" Launch the settings dialog widget to configure account information
		"""
		dialog = SettingsDialog(self)
		if dialog.exec_():
			self.reset()
		#self.setFilter()
#		self.tableView.model().sourceModel().select()

	def importDialog(self):
		""" Launch the import dialog
		"""
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

		with utils.showWaitCursor():
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

	def recordSelectionChanged(self):
		""" Only enable buttons if a selection has been made
		""" 
		enable = len(self.tableView.selectionModel().selectedRows()) > 0
		self.toggleCheckButton.setEnabled(enable)
		self.deleteButton.setEnabled(enable)

	def selectedRecordIds(self):
		""" Returns a list of all currently selected recordIds
		"""
		proxyModel = self.tableView.model()
		recordIds = []

		for proxyIndex in self.tableView.selectionModel().selectedRows():
			index = proxyModel.sourceModel().index(proxyModel.mapToSource(proxyIndex).row(), enum.kRecordColumn_RecordId)
			recordIds.append(index.data().toPyObject())
		return recordIds

	def enableRemoveTagButton(self):
		enable = len(self.tagView.selectionModel().selectedRows()) > 0
		self.removeTagButton.setEnabled(enable)

	def controlKeyPressed(self, key):
		""" Control key has been pressed

			If we have a single row displayed, then toggle the status
			If this results in the model having no records then
			reset the QLineEdit that triggered the call.
		"""
		proxyModel = self.tableView.model()

		if proxyModel and key == QtCore.Qt.Key_Space:
			if proxyModel.rowCount() == 1:
				self.tableView.selectAll()
				self.toggleSelected()

			if proxyModel.rowCount() == 0 and isinstance(self.sender(), QtGui.QLineEdit):
				self.sender().clear()

	def deleteRecords(self):
		""" Delete selected records
		"""
		selectionModel = self.tableView.selectionModel()
		proxyModel = self.tableView.model()

		if QtGui.QMessageBox.question(
				self, 'Delete Records',
				'Are you sure you want to delete %d rows?' % len(selectionModel.selectedRows()),
				QtGui.QMessageBox.Yes|QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
			return

		with utils.showWaitCursor():
			indexes = [proxyModel.mapToSource(index) for index in selectionModel.selectedRows()]
			if not proxyModel.sourceModel().deleteRecords(indexes):
				QtGui.QMessageBox.critical(self, 'Database Error',
					proxyModel.sourceModel().lastError().text(), QtGui.QMessageBox.Ok)

	@contextmanager
	def keepSelection(self):
		""" Context manager to preserve table selection. This is usually required
			when calling select on the model - as this causes a reset of the model.

			There should be a better way of doing this, but the only accurate means
			of determining what rows were selected is by saving the recordIds before
			the yield, and then restoring them with a call to match.
			"""
		try:
			# Save selection
			selectedRecords = self.selectedRecordIds()
			selectionMode = self.tableView.selectionMode()
			yield
		finally:
			# Set this temporarily so that we can select more than one row
			self.tableView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
			proxyModel = self.tableView.model()

			for recordId in selectedRecords:
				currentIndex = proxyModel.sourceModel().index(0, enum.kRecordColumn_RecordId)
				match = proxyModel.sourceModel().match(currentIndex, QtCore.Qt.DisplayRole, recordId, 1, QtCore.Qt.MatchExactly)
				if match:
					self.tableView.selectRow(proxyModel.mapFromSource(match[0]).row())

			self.tableView.setSelectionMode(selectionMode)
			
			selected = self.tableView.selectionModel().selectedRows()

			# Scroll to first selected row
			if selected:
				self.tableView.scrollTo(selected[0], QtGui.QAbstractItemView.EnsureVisible)

	def populateDates(self):
		query = QtSql.QSqlQuery("""
			SELECT MIN(date), 
				   MAX(date),  
				   MAX(insertdate)
			  FROM records
			 WHERE userid=%d
			""" % db.userId)

		if query.next():
			startDate = query.value(0).toDate()
			endDate = query.value(1).toDate()
			maxInsertDateTime = query.value(2).toDateTime()

			self.startDateEdit.setDateRange(startDate, endDate)
			self.endDateEdit.setDateRange(startDate, endDate)

			self.startDateEdit.setDate(startDate)
			self.endDateEdit.setDate(endDate)
			self.maxInsertDate = maxInsertDateTime

	@utils.showWaitCursorDecorator
	def toggleSelected(self, *args):

		""" Toggle checked status on all selected rows in view.
		"""
		selectionModel = self.tableView.selectionModel()
		proxyModel = self.tableView.model()

		with blockSignals(self.tableView.model().sourceModel()):
			for proxyIndex in selectionModel.selectedRows():
				# Need the index of checked column
				proxyIndex = proxyModel.index(proxyIndex.row(), enum.kRecordColumn_Checked)
				index = proxyModel.mapToSource(proxyIndex)
	
				if index.data(QtCore.Qt.CheckStateRole).toPyObject() == QtCore.Qt.Checked:
					proxyModel.sourceModel().setData(index, QtCore.QVariant(QtCore.Qt.Unchecked), QtCore.Qt.CheckStateRole)
				elif index.data(QtCore.Qt.CheckStateRole).toPyObject() == QtCore.Qt.Unchecked:
					proxyModel.sourceModel().setData(index, QtCore.QVariant(QtCore.Qt.Checked), QtCore.Qt.CheckStateRole)
		
		self.tableView.model().sourceModel().reset()

	def reset(self):
		""" Reset all filters and combo boxes to a default state
		"""
		with utils.blockSignals(self.__signalsToBlock):
			self.populateDates()
			self.checkedCombo.setCurrentIndex(enum.kCheckedStatus_All)
			self.tagsCombo.setCurrentIndex(enum.kCheckedStatus_All)
			self.dateCombo.setCurrentIndex(enum.kDate_PreviousYear)
			self.selectDateRange()
			self.accountCombo.clearAll()
			self.inoutCombo.setCurrentIndex(enum.kInOutStatus_All)
			self.amountEdit.clear()
			self.descEdit.clear()
			self.endDateEdit.setEnabled(True)
			self.tableView.sortByColumn(enum.kRecordColumn_Date, QtCore.Qt.DescendingOrder)

		# ClearFilters
		self.tableView.model().clearFilters()

		# Need signals to clear highlight filter on model
		self.scrolltoEdit.clear()

		# Reset tagView - block signals as we're calling setFilter anyway
		tagModel = self.tagView.model().sourceModel()
		tagModel.blockSignals(True)
		tagModel.clearSelection()
		tagModel.blockSignals(False)
		#self.setFilter()
		self.tableView.model().sourceModel().select()

	def dateRangeSelected(self):
		""" Date combo has been changed. Set the date fields and refresh the records model
		"""
		self.selectDateRange()
#		self.setFilter()

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
		inTotal = 0.0
		outTotal = 0.0

		model = self.tableView.model().sourceModel()
		for row in xrange(model.rowCount()):
			amount = model.index(row, enum.kRecordColumn_Amount).data(QtCore.Qt.UserRole).toPyObject()
			if amount > 0.0:
				inTotal += amount
			else:
				outTotal += abs(amount)

		self.inTotalLabel.setText(QtCore.QString("%L1").arg(inTotal, 0, 'f', 2))
		self.outTotalLabel.setText(QtCore.QString("%L1").arg(outTotal, 0, 'f', 2))
		self.recordCountLabel.setText('%d / %d' % (self.tableView.model().rowCount(), model.rowCount()))

	@utils.showWaitCursorDecorator
	def recordsChanged(self, *args):
		print 'recordsChanged called', self.sender()

		self.updateTagFilter()

		self.tagView.updateGeometry()
		self.tagView.resizeColumnsToContents()
		self.tableView.resizeColumnsToContents()
		
		self.displayRecordCount()

	def tagModelChanged(self):
		""" Tag model has changed - call select on record model to refresh the changes (in tag column)
			Note: calling setFilter is a bad idea as we'll enter circular hell
		"""
		#TODO: fix me
		with self.keepSelection():
			self.tableView.model().sourceModel().select()

	def updateTagFilter(self):
		""" Tell the tag model to limit tag amounts to current displayed records
		"""
		recordIds = []
		model = self.tableView.model()

		for i in xrange(model.rowCount()):
			recordIds.append(model.index(i, enum.kRecordColumn_RecordId).data().toPyObject())

		self.tagView.model().sourceModel().setRecordFilter(recordIds)


	def addTag(self):
		""" Add a new tag to the tag model and assign any selected records
		"""
		tagName, ok = QtGui.QInputDialog.getText(self, 'New Tag', 'Tag', QtGui.QLineEdit.Normal)

		proxyModel = self.tagView.model()
		if ok and tagName:
			match = proxyModel.match(proxyModel.index(0, enum.kTagsColumn_TagName), QtCore.Qt.DisplayRole, tagName, 1, QtCore.Qt.MatchExactly)
			if match:
				QtGui.QMessageBox.critical( self, 'Tag Error', 'Tag already exists!', QtGui.QMessageBox.Ok)
				return

		# Assign selected records with the new tag
		tagId = proxyModel.sourceModel().addTag(tagName)
		proxyModel.sourceModel().addRecordTags(tagId, self.selectedRecordIds())

	def removeTag(self):
		proxyModel = self.tagView.model()
		for proxyIndex in self.tagView.selectionModel().selectedRows():
			assignedRecords = proxyModel.sourceModel().index(proxyModel.mapToSource(proxyIndex).row(), enum.kTagsColumn_RecordIds).data().toPyObject()
			if assignedRecords:
				if QtGui.QMessageBox.question(
						self, 'Delete Tags',
						'There are %d records assigned to this tag\nSure you want to delete it?' % len(assignedRecords),
						QtGui.QMessageBox.Yes|QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
					continue
			tagId = proxyModel.sourceModel().index(proxyModel.mapToSource(proxyIndex).row(), enum.kTagsColumn_TagId).data().toPyObject()
			proxyModel.sourceModel().removeTag(tagId)


	def tagEditPopup(self, pos):
		self.tableView.viewport().mapToGlobal(pos)

		tagList = TagListWidget(self)
		tagList.setPersistEditor(QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier)
		tagList.itemChanged.connect(self.saveTagChanges)

		selectedRecordIds = set(self.selectedRecordIds())
		model = self.tagView.model()
		for row in xrange(model.rowCount()):
			tagId = model.index(row, enum.kTagsColumn_TagId).data().toPyObject()
			tagName = model.index(row, enum.kTagsColumn_TagName).data().toPyObject()
			tagRecordIds = model.index(row, enum.kTagsColumn_RecordIds).data().toPyObject()

			item = QtGui.QListWidgetItem(tagName)
			item.setData(QtCore.Qt.UserRole, tagId)

			if selectedRecordIds and selectedRecordIds.issubset(tagRecordIds):
				item.setCheckState(QtCore.Qt.Checked)
				tooltip = 'all %d selected records have tag %r' %  (len(selectedRecordIds), str(tagName))

			elif selectedRecordIds and selectedRecordIds.intersection(tagRecordIds):
				item.setCheckState(QtCore.Qt.PartiallyChecked)
				tooltip = '%d of %d selected records have tag %r' %  (
						len(selectedRecordIds.intersection(tagRecordIds)),
						len(selectedRecordIds), str(tagName))
			else:
				item.setCheckState(QtCore.Qt.Unchecked)
				tooltip = 'no selected records have tag %r' % str(tagName)
			
			item.setData(QtCore.Qt.ToolTipRole, tooltip)
			tagList.addItem(item)

		action = QtGui.QWidgetAction(self)
		action.setDefaultWidget(tagList)

		menu = QtGui.QMenu(self)
		menu.addAction(action)
		menu.exec_(self.tableView.viewport().mapToGlobal(pos))

	def saveTagChanges(self, item):
		""" Save tag changes to tag model
		"""
		checkState = item.data(QtCore.Qt.CheckStateRole).toPyObject()
		tagId = item.data(QtCore.Qt.UserRole).toPyObject()

		if checkState == QtCore.Qt.Unchecked:
			self.tagView.model().sourceModel().removeRecordTags(tagId, self.selectedRecordIds())
		else:
			self.tagView.model().sourceModel().addRecordTags(tagId, self.selectedRecordIds())

		if item.listWidget().persistEditor() == False or len(self.selectedRecordIds()) == 0:
			# If there's no selection available then close the tag menu
			item.listWidget().parent().close()

	def scrollTo(self, text):
		# Tell the model to highlight or un-highlight matching rows
		self.tableView.model().sourceModel().highlightText(text)

		if text:
			currentIndex = self.tableView.model().index(0, enum.kRecordColumn_Description)
			matches = self.tableView.model().match(currentIndex, QtCore.Qt.DisplayRole, text)
			if matches:
				self.tableView.scrollTo(matches[0], QtGui.QAbstractItemView.EnsureVisible)

class TagListWidget(QtGui.QListWidget):
	""" Simple extension to QListWidget to allow persistence of editor
		when used in QMenu popup
	""" 
	def __init__(self, parent=None):
		super(TagListWidget, self).__init__(parent=parent)
		self.__persistEditor = False

	def setPersistEditor(self, persist):
		self.__persistEditor = persist

	def persistEditor(self):
		return self.__persistEditor