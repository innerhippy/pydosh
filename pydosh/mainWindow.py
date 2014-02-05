from PySide import QtGui, QtCore, QtSql, __version__ as pyside_version
from contextlib  import contextmanager
import operator
import re

from pydosh import __version__
from database import db
from ui_pydosh import Ui_pydosh
import currency
import utils
import models
import dialogs
import stylesheet
import enum
import pydosh_rc

class PydoshWindow(Ui_pydosh, QtGui.QMainWindow):
	__operatorMap = {
		'=':  operator.eq,
		'>':  operator.gt,
		'<':  operator.lt,
		'>=': operator.ge,
		'<=': operator.le
	}

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

		self.connectionStatusText.setText('connected to %s@%s' % (db.database, db.hostname))

		amountValidator = QtGui.QRegExpValidator(QtCore.QRegExp("[<>=0-9.]*"), self)
		self.amountEdit.setValidator(amountValidator)

		self.startDateEdit.setCalendarPopup(True)
		self.endDateEdit.setCalendarPopup(True)

		self.addActions()

		# Date ranges
		self.maxInsertDate = None
		self.populateDates()

		# Set up record model
		recordModel = models.RecordModel(self)
		recordModel.setTable('records')
		recordModel.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
		recordProxyModel = models.RecordProxyModel(self)

		# "you should not update the source model through
		#  the proxy model when dynamicSortFilter is true"
		recordProxyModel.setDynamicSortFilter(False)
		recordProxyModel.setSourceModel(recordModel)

		self.tableView.setModel(recordProxyModel)
		recordModel.select()

		# Set up record view
		self.tableView.verticalHeader().hide()
		self.tableView.setColumnHidden(enum.kRecordColumn_RecordId, True)
		self.tableView.setColumnHidden(enum.kRecordColumn_AccountTypeId, True)
		self.tableView.setColumnHidden(enum.kRecordColumn_CheckDate, True)
		self.tableView.setColumnHidden(enum.kRecordColumn_RawData, True)
		self.tableView.setColumnHidden(enum.kRecordColumn_InsertDate, True)
		self.tableView.setColumnHidden(enum.kRecordColumn_Currency, True)
		self.tableView.setSortingEnabled(True)
		self.tableView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tableView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		self.tableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		self.tableView.horizontalHeader().setResizeMode(enum.kRecordColumn_Description, QtGui.QHeaderView.Stretch)
		self.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

		# Set up tag model
		tagModel = models.TagModel(self)
		tagProxyModel = models.TagProxyModel(self)
		tagProxyModel.setSourceModel(tagModel)
		tagProxyModel.sort(enum.kTagsColumn_Amount_out, QtCore.Qt.AscendingOrder)
		self.tagView.setModel(tagProxyModel)

		# Set up tag view
		self.tagView.verticalHeader().hide()
		self.tagView.setColumnHidden(enum.kTagsColumn_TagId, True)
		self.tagView.setColumnHidden(enum.kTagsColumn_RecordIds, True)
		self.tagView.setSortingEnabled(True)
		self.tagView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.tagView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.tagView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.tagView.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		self.tagView.setShowGrid(False)

		# Set up account model
		self.accountCombo.setDefaultText('all')
		self.populateAccounts()

		# Set delays on searchlinededit widgets
		self.descEdit.setDelay(400)
		self.amountEdit.setDelay(400)

		# Set up connections
		self.scrolltoEdit.textChanged.connect(self.scrollTo)
		self.toggleCheckButton.clicked.connect(self.toggleSelected)
		self.deleteButton.clicked.connect(self.deleteRecords)
		self.dateCombo.currentIndexChanged.connect(self.setDateRange)
		self.reloadButton.clicked.connect(self.reset)
		self.addTagButton.clicked.connect(self.addTag)
		self.removeTagButton.clicked.connect(self.removeTag)
		recordModel.dataChanged.connect(self.updateTagFilter)
		recordProxyModel.filterChanged.connect(self.updateTagFilter)
		recordProxyModel.modelReset.connect(self.updateTagFilter)
		selectionModel = self.tableView.selectionModel()
		selectionModel.selectionChanged.connect(self.recordSelectionChanged)
		self.tableView.customContextMenuRequested.connect(self.tagEditPopup)
		tagModel.tagsChanged.connect(self.tagModelChanged)
		tagModel.selectionChanged.connect(recordProxyModel.setTagFilter)
		selectionModel = self.tagView.selectionModel()
		selectionModel.selectionChanged.connect(self.enableRemoveTagButton)
		self.startDateEdit.dateChanged.connect(recordProxyModel.setStartDate)
		self.endDateEdit.dateChanged.connect(self.endDateChanged)
		self.endDateEdit.dateChanged.connect(recordProxyModel.setEndDate)
		self.accountCombo.selectionChanged.connect(self.accountSelectionChanged)
		self.tagsCombo.currentIndexChanged.connect(self.tagSelectionChanged)
		self.checkedCombo.currentIndexChanged.connect(self.checkedSelectionChanged)
		self.inoutCombo.currentIndexChanged.connect(self.inOutSelectionChanged)
		self.descEdit.editingFinshed.connect(recordProxyModel.setDescriptionFilter)
		self.amountEdit.controlKeyPressed.connect(self.controlKeyPressed)
		self.amountEdit.editingFinshed.connect(self.amountFilterChanged)

		self.reset()

	def accountSelectionChanged(self, items):
		""" Tell the proxy filter to filter on selected account ids
		"""
		accountIds = [self.accountCombo.itemData(self.accountCombo.findText(item)) for item in items]
		self.tableView.model().setAccountFilter(accountIds)

	def tagSelectionChanged(self, index):
		""" Basic tag filter (has tags or not)
		"""
		state = self.tagsCombo.itemData(index, QtCore.Qt.UserRole)
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
		state = self.checkedCombo.itemData(index, QtCore.Qt.UserRole)
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
		state = self.inoutCombo.itemData(index, QtCore.Qt.UserRole)
		if state == enum.kInOutStatus_In:
			value = True
		elif state == enum.kInOutStatus_Out:
			value = False
		else:
			value = None
		self.tableView.model().setCreditFilter(value)

	def amountFilterChanged(self, text):
		if text:
			if re.match('[<>=]', text):
				# looks like we have operators, test validity and amount
				match = re.match('^(=|>|<|>=|<=)([\d\.]+)', text)
				if match:
					opStr, amount = match.groups()
					if opStr in self.__operatorMap:
						self.tableView.model().setAmountFilter(amount, self.__operatorMap[opStr])
				return

		self.tableView.model().setAmountFilter(text)

	def showAbout(self):
		""" Show 'about' info
		"""
		QtGui.QMessageBox.about(self,
			'About pydosh',
			"<html><p><h2>pydosh</h2></p>"
			"<p>version %s</p>"
			"<p>by Will Hall <a href=\"mailto:will@innerhippy.com\">will@innerhippy.com</a></p>"
			"<p>Copywrite (c) 2013.</p>"
			"<p>Written using Qt %s, PySide %s</p>"
			"<p><a href=\"http://www.innerhippy.com\">www.innerhippy.com</a></p>"
			"enjoy!</html>" % (__version__, QtCore.__version__, pyside_version)
			)

	def endDateChanged(self, date):
		""" End date has changed - if date mode is "previous" month,
			the update start date accordingly
		"""
		if self.dateCombo.currentIndex() == enum.kDate_PreviousMonth:
			self.startDateEdit.setDate(self.endDateEdit.date().addMonths(-1))

	@utils.showWaitCursorDecorator
	def setDateRange(self, index=None):
		""" Set date fields according to date combo selection mode
		"""
		if index is None:
			index = self.dateCombo.currentIndex()

		proxyModel = self.tableView.model()

		if index == enum.kDate_All:
			self.startDateEdit.setEnabled(True)
			self.endDateEdit.setEnabled(True)

			self.startDateEdit.setDate(self.startDateEdit.minimumDate())
			self.endDateEdit.setDate(self.endDateEdit.maximumDate())

		elif index == enum.kDate_PreviousMonth:
			self.endDateEdit.setEnabled(True)
			self.startDateEdit.setEnabled(False)

			self.endDateEdit.setDate(self.endDateEdit.maximumDate())
			self.startDateEdit.setDate(self.endDateEdit.date().addMonths(-1))

		elif index == enum.kDate_PreviousYear:
			self.startDateEdit.setEnabled(True)
			self.endDateEdit.setEnabled(True)

			self.endDateEdit.setDate(self.endDateEdit.maximumDate())
			self.startDateEdit.setDate(self.endDateEdit.date().addYears(-1))

		elif index == enum.kdate_LastImport:
			self.startDateEdit.setEnabled(False)
			self.endDateEdit.setEnabled(False)

			proxyModel.setInsertDate(insertDate=self.maxInsertDate)

			startDate = QtCore.QDate()
			endDate = QtCore.QDate()

			# Find the min/max dates for the last import from the proxy model
			for row in xrange(proxyModel.rowCount()):
				dateForRow = proxyModel.index(row, enum.kRecordColumn_Date).data(QtCore.Qt.UserRole)
				if not endDate.isValid() or dateForRow > endDate:
					endDate = dateForRow
				if not startDate.isValid() or dateForRow < startDate:
					startDate = dateForRow

			# This is for information only, so don't trigger a query on the proxy
			with utils.signalsBlocked(self.endDateEdit, self.startDateEdit):
				self.startDateEdit.setDate(startDate)
				self.endDateEdit.setDate(endDate)

	def settingsDialog(self):
		""" Launch the settings dialog widget to configure account information
		"""
		dialog = dialogs.SettingsDialog(self)
		dialog.exec_()

	def importDialog(self):
		""" Launch the import dialog
		"""
		# try and set last import directory
		settings = QtCore.QSettings()
		importDir = settings.value("options/importdirectory")

		if not importDir:
			importDir = QtCore.QDir.homePath()

		dialog = QtGui.QFileDialog(self, 'Open File', importDir, "*.csv")
		dialog.setFileMode(QtGui.QFileDialog.ExistingFiles)

		if not dialog.exec_():
			return

		fileNames = [QtCore.QFileInfo(f).fileName() for f in dialog.selectedFiles()]

		# Save the settings for next time
		settings.setValue('options/importdirectory', dialog.directory().absolutePath())

		dialog = dialogs.ImportDialog(dialog.selectedFiles(), self)
		dialog.setWindowTitle(', '.join(fileNames))
		dialog.accepted.connect(self.importClosed)
		dialog.show()

	def importClosed(self):
		""" Statements have been imported successfully - refresh models
		"""
		self.tableView.model().sourceModel().select()
		self.populateAccounts()
		self.populateDates()
		self.setDateRange()

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
			recordIds.append(index.data())
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

			if proxyModel.rowCount() == 0:
				self.amountEdit.clear()

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

			# Finally, re-populate accounts and date range in case this has changed
			self.populateAccounts()
			self.populateDates()
			self.setDateRange()

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

	def populateAccounts(self):
		""" Populate account data for the current user
		"""
		self.accountCombo.clear()
		query = QtSql.QSqlQuery("""
		    SELECT accounttypeid, accountname
		      FROM accounttypes
		     WHERE accounttypeid IN (
		           SELECT DISTINCT accounttypeid
		                      FROM records
		                     WHERE userid=%s)
		  ORDER BY accountname
		""" % db.userId)

		while query.next():
			self.accountCombo.addItem(query.value(1), query.value(0))

	def populateDates(self):
		""" Set date fields to min and max values
		"""
		query = QtSql.QSqlQuery("""
			SELECT MIN(date),
				   MAX(date),
				   MAX(insertdate)
			  FROM records
			 WHERE userid=%d
			""" % db.userId)

		if query.next():
			startDate = query.value(0)
			endDate = query.value(1)
			maxInsertDateTime = query.value(2)

			self.startDateEdit.setDateRange(startDate, endDate)
			self.endDateEdit.setDateRange(startDate, endDate)
			self.maxInsertDate = maxInsertDateTime

	@utils.showWaitCursorDecorator
	def toggleSelected(self, *args):

		""" Toggle checked status on all selected rows in view.
		"""
		selectionModel = self.tableView.selectionModel()
		proxyModel = self.tableView.model()
		modelIndexes = [proxyModel.mapToSource(index) for index in selectionModel.selectedRows()]

		with self.keepSelection():
			proxyModel.sourceModel().toggleChecked(modelIndexes)

	@utils.showWaitCursorDecorator
	def reset(self, *args):
		""" Reset all filters and combo boxes to a default state
		"""
		signalsToBlock = (
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
				self.tableView.model(),
		)

		with utils.signalsBlocked(signalsToBlock):
			self.tagView.model().sourceModel().clearSelection()
			self.tableView.model().clearFilters()

			self.dateCombo.setCurrentIndex(enum.kDate_PreviousMonth)

			# Signals blocked so need to reset filter manually
			self.setDateRange()
			self.tableView.model().setStartDate(self.startDateEdit.date())
			self.tableView.model().setEndDate(self.endDateEdit.date())

			self.checkedCombo.setCurrentIndex(enum.kCheckedStatus_All)
			self.tagsCombo.setCurrentIndex(enum.kCheckedStatus_All)
			self.inoutCombo.setCurrentIndex(enum.kInOutStatus_All)
			self.accountCombo.clearAll()
			self.amountEdit.clear()
			self.descEdit.clear()

			self.tableView.sortByColumn(enum.kRecordColumn_Date, QtCore.Qt.AscendingOrder)
			self.tagView.sortByColumn(enum.kTagsColumn_TagName, QtCore.Qt.AscendingOrder)

		self.tableView.model().sourceModel().select()
		# Need signals to clear highlight filter on model
		self.scrolltoEdit.clear()
		self.tableView.model().reset()

		self.tagView.resizeColumnsToContents()
		self.tableView.resizeColumnsToContents()

	def addActions(self):
		menu = self.menuBar().addMenu('&Settings')

		action = menu.addAction(QtGui.QIcon(':/icons/import.png'), '&Import')
		action.setShortcut('Alt+i')
		action.setStatusTip('Import Bank statements')
		action.triggered.connect(self.importDialog)

		action = menu.addAction(QtGui.QIcon(':/icons/wrench.png'), '&Accounts')
		action.setShortcut('Alt+s')
		action.setStatusTip('Account setup')
		action.triggered.connect(self.settingsDialog)

		styleMenu = menu.addMenu(QtGui.QIcon(':/icons/brush.png'), 'Style')
		for style in stylesheet.styleSheetNames():
			styleMenu.addAction(style, self.setStyle)

		action = menu.addAction(QtGui.QIcon(':/icons/exit.png'), '&Quit')
		action.setShortcut('Alt+q')
		action.setStatusTip('Exit the program')
		action.triggered.connect(self.close)

		menu = self.menuBar().addMenu('&Help')
		action = menu.addAction(QtGui.QIcon(':/icons/help.png'), '&About')
		action.setStatusTip('About')
		action.triggered.connect(self.showAbout)

	def setStyle(self):
		""" Triggered from menu action when user selects a style/theme
		"""
		action = self.sender()
		if action:
			stylesheet.setStylesheet(action.text())

	def displayRecordCount(self):
		inTotal = 0.0
		outTotal = 0.0

		model = self.tableView.model()
		for row in xrange(model.rowCount()):
			amount = model.index(row, enum.kRecordColumn_Amount).data(QtCore.Qt.UserRole)
			if amount > 0.0:
				inTotal += amount
			else:
				outTotal += abs(amount)

		self.inTotalLabel.setText(currency.toCurrencyStr(inTotal))
		self.outTotalLabel.setText(currency.toCurrencyStr(outTotal))
		self.recordCountLabel.setText('%d / %d' % (model.rowCount(), self.tableView.model().sourceModel().rowCount()))

	def tagModelChanged(self):
		""" Tag model has changed - call select on record model to refresh the changes (in tag column)
			Note: calling setFilter is a bad idea as we'll enter circular hell
		"""
		with self.keepSelection():
			self.tableView.model().sourceModel().select()

	@utils.showWaitCursorDecorator
	def updateTagFilter(self, *args):
		""" Tell the tag model to limit tag amounts to current displayed records
		"""
		recordIds = []
		model = self.tableView.model()

		for i in xrange(model.rowCount()):
			recordIds.append(model.index(i, enum.kRecordColumn_RecordId).data())

		self.tagView.model().sourceModel().setRecordFilter(recordIds)
		self.tagView.resizeColumnsToContents()
		self.displayRecordCount()


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
		self.tagView.resizeColumnsToContents()

	def removeTag(self):
		""" Delete a tag - ask for confirmation if tag is currently assigned to records
		"""
		proxyModel = self.tagView.model()
		for proxyIndex in self.tagView.selectionModel().selectedRows():
			assignedRecords = proxyModel.sourceModel().index(proxyModel.mapToSource(proxyIndex).row(), enum.kTagsColumn_RecordIds).data()
			if assignedRecords:
				if QtGui.QMessageBox.question(
						self, 'Delete Tags',
						'There are %d records assigned to this tag\nSure you want to delete it?' % len(assignedRecords),
						QtGui.QMessageBox.Yes|QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
					continue
			with utils.showWaitCursor():
				tagId = proxyModel.sourceModel().index(proxyModel.mapToSource(proxyIndex).row(), enum.kTagsColumn_TagId).data()
				proxyModel.sourceModel().removeTag(tagId)

		self.tagView.resizeColumnsToContents()

	def tagEditPopup(self, pos):
		self.tableView.viewport().mapToGlobal(pos)

		tagList = TagListWidget(self)
		tagList.setPersistEditor(QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier)
		tagList.itemChanged.connect(self.saveTagChanges)

		selectedRecordIds = set(self.selectedRecordIds())
		model = self.tagView.model()

		for row in xrange(model.rowCount()):
			tagId = model.index(row, enum.kTagsColumn_TagId).data()
			tagName = model.index(row, enum.kTagsColumn_TagName).data()
			tagRecordIds = model.index(row, enum.kTagsColumn_RecordIds).data()

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

		if tagList.count():
			action = QtGui.QWidgetAction(self)
			action.setDefaultWidget(tagList)
			menu = QtGui.QMenu(self)
			menu.addAction(action)
			menu.exec_(self.tableView.viewport().mapToGlobal(pos))

			if not self.selectedRecordIds():
				if not self.amountEdit.text() and self.descEdit.text():
					self.descEdit.clear()
					self.descEdit.setFocus(QtCore.Qt.OtherFocusReason)
				elif not self.descEdit.text() and self.amountEdit.text():
					self.amountEdit.clear()
					self.amountEdit.setFocus(QtCore.Qt.OtherFocusReason)

	@utils.showWaitCursorDecorator
	def saveTagChanges(self, item):
		""" Save tag changes to tag model
		"""
		checkState = item.data(QtCore.Qt.CheckStateRole)
		tagId = item.data(QtCore.Qt.UserRole)

		if checkState == QtCore.Qt.Unchecked:
			self.tagView.model().sourceModel().removeRecordTags(tagId, self.selectedRecordIds())
		else:
			self.tagView.model().sourceModel().addRecordTags(tagId, self.selectedRecordIds())

		if item.listWidget().persistEditor() == False or len(self.selectedRecordIds()) == 0:
			# If there's no selection available then close the tag menu
			item.listWidget().parent().close()

		self.displayRecordCount()

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
