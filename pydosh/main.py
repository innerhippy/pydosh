from contextlib  import contextmanager
from version import __VERSION__
from PyQt4 import QtGui, QtCore, QtSql
from utils import showWaitCursorDecorator, showWaitCursor
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
		self.accountCombo.selectionChanged.connect(self.setFilter)
		self.checkedCombo.currentIndexChanged.connect(self.setFilter)
		self.tagsCombo.currentIndexChanged.connect(self.setFilter)
		self.inoutCombo.currentIndexChanged.connect(self.setFilter)
		self.descEdit.textChanged.connect(self.setFilter)
		self.amountEdit.textChanged.connect(self.setFilter)
		self.amountEdit.controlKeyPressed.connect(self.controlKeyPressed)
		self.toggleCheckButton.clicked.connect(self.toggleSelected)
		self.deleteButton.clicked.connect(self.deleteRecords)
		self.dateCombo.currentIndexChanged.connect(self.dateRangeSelected)
		self.startDateEdit.dateChanged.connect(self.setFilter)
		self.endDateEdit.dateChanged.connect(self.setFilter)
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
				self.amountEdit,
				self.dateCombo,
				self.startDateEdit,
				self.endDateEdit,
		)

		self.filterTagIds = set()

		with self.blockAllSignals():

			model = RecordModel(self)
			model.setTable('records')
			model.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
			model.dataChanged.connect(self.setFilter)
			model.select()

			proxyModel = SortProxyModel(self)
			proxyModel.setSourceModel(model)
			proxyModel.sort(enum.kRecordColumn_Date, QtCore.Qt.AscendingOrder)

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

			self.tableView.horizontalHeader().setResizeMode(enum.kRecordColumn_Description, QtGui.QHeaderView.Stretch)
			self.tableView.selectionModel().selectionChanged.connect(self.recordSelectionChanged)

			self.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
			self.tableView.customContextMenuRequested.connect(self.tagEditPopup)

			model = TagModel(self)
			model.tagsChanged.connect(self.tagModelChanged)
			model.selectionChanged.connect(self.setTagFilter)
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

	def selectDateRange(self):
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

	def settingsDialog(self):
		""" Launch the settings dialog widget to configure account information
		"""
		dialog = SettingsDialog(self)
		dialog.exec_()
		self.setFilter()

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

		with showWaitCursor():
			indexes = [proxyModel.mapToSource(index) for index in selectionModel.selectedRows()]
			if proxyModel.sourceModel().deleteRecords(indexes):
				self.accountCombo.model().select()
			else:
				QtGui.QMessageBox.critical(self, 'Database Error',
					proxyModel.sourceModel().lastError().text(), QtGui.QMessageBox.Ok)

	@contextmanager
	def blockAllSignals(self):
		try:
			for widget in self.__signalsToBlock:
				widget.blockSignals(True)
			yield
		finally:
			for widget in self.__signalsToBlock:
				widget.blockSignals(False)

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

		""" Toggle checked status on all selected rows in view.
		"""
		# Get recordids from all selected rows
		selectionModel = self.tableView.selectionModel()
		if selectionModel is None:
			return

		proxyModel = self.tableView.model()
		indexes = [proxyModel.mapToSource(proxyIndex) for proxyIndex in selectionModel.selectedRows()]
		if not proxyModel.sourceModel().setItemsChecked(indexes):
			QtGui.QMessageBox.critical(self, 'Database Error', 
					proxyModel.sourceModel().lastError().text(), QtGui.QMessageBox.Ok)

	def reset(self):
		if self.tableView.model() is None:
			return

		with self.blockAllSignals():
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

		# Reset tagView - block signals as we're calling setFilter anyway
		tagModel = self.tagView.model().sourceModel()
		tagModel.blockSignals(True)
		tagModel.clearSelection()
		tagModel.blockSignals(False)
		self.setFilter()

	def dateRangeSelected(self):
		""" Date combo has been changed. Set the date fields and refresh the records model
		"""
		self.selectDateRange()
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
		model = self.tableView.model()

		if model:
			numRecords = model.rowCount()

			query = QtSql.QSqlQuery('SELECT COUNT(*) FROM records WHERE userid=%d' % db.userId)
			query.next()
			totalRecords = query.value(0).toPyObject()

			for i in xrange(numRecords):
				amount, _ = model.sourceModel().record(i).value(enum.kRecordColumn_Amount).toDouble()
				if amount > 0.0:
					inTotal += amount
				else:
					outTotal += abs(amount)

		self.inTotalLabel.setText(QtCore.QString("%L1").arg(inTotal, 0, 'f', 2))
		self.outTotalLabel.setText(QtCore.QString("%L1").arg(outTotal, 0, 'f', 2))
		self.recordCountLabel.setText('%d / %d' % (numRecords, totalRecords))

	@showWaitCursorDecorator
	def setFilter(self, *args):
		model = self.tableView.model()

		if model is None:
			return

		queryFilter = []

		# Account filter
		accountIds = [index.data(QtCore.Qt.UserRole).toPyObject() for index in self.accountCombo.checkedIndexes()]
		if accountIds:
			queryFilter.append('r.accounttypeid in (%s)' % ', '.join(str(acid) for acid in accountIds))

		# Date filter
		if self.dateCombo.itemData(self.dateCombo.currentIndex(), QtCore.Qt.UserRole).toPyObject() == enum.kdate_LastImport:
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

		# Basic tag filter
		state = self.tagsCombo.itemData(self.tagsCombo.currentIndex(), QtCore.Qt.UserRole).toPyObject()
		if state == enum.kTagCombo_With:
			queryFilter.append('t.tagname is not null')
		elif state == enum.kTagCombo_Without:
			queryFilter.append('t.tagname is null')

		# checked state filter
		state = self.checkedCombo.itemData(self.checkedCombo.currentIndex(), QtCore.Qt.UserRole).toPyObject()
		if state == enum.kCheckedStatus_Checked:
			queryFilter.append('r.checked=1')
		elif state == enum.kCheckedStatus_UnChecked:
			queryFilter.append('r.checked=0')

		# money in/out filter
		state = self.inoutCombo.itemData(self.inoutCombo.currentIndex(), QtCore.Qt.UserRole).toPyObject()
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
					"(CAST(r.amount AS char(10)) LIKE '%s%%' OR CAST(r.amount AS char(10)) LIKE '-%s%%')" %
					(amountFilter, amountFilter))

		if self.filterTagIds:
			queryFilter.append("""
				r.recordid IN (
					SELECT recordid
					FROM recordtags
					WHERE tagid in (%s))
				""" % ', '.join([str(tagid) for tagid in self.filterTagIds]))

		with self.keepSelection():
			model.sourceModel().setFilter('\nAND '.join(queryFilter))
		#print model.sourceModel().query().lastQuery().replace(' AND ', '').replace('\n', ' ')

		self.updateTagFilter()

		self.tagView.updateGeometry()
		self.tableView.resizeColumnsToContents()
		self.tagView.resizeColumnsToContents()
		self.displayRecordCount()

	def tagModelChanged(self):
		""" Tag model has changed - call select on record model to refresh the changes (in tag column)
			Note: calling setFilter is a bad idea as we'll enter circular hell
		"""
		with self.keepSelection():
			self.tableView.model().sourceModel().select()

	def updateTagFilter(self):
		""" Tell the tag model to limit tag amounts to current displayed records
		"""
		recordIds = []
		model = self.tableView.model().sourceModel()

		for i in xrange(model.rowCount()):
			recordIds.append(model.index(i, enum.kRecordColumn_RecordId).data().toPyObject())

		self.tagView.model().sourceModel().setFilter(recordIds)


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

	def setTagFilter(self, tagIds):
		""" Filter model by tags in response to tagView selection changed
		"""
		self.filterTagIds = tagIds
		self.setFilter()


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