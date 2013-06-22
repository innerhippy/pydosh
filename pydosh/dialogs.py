import re
from PyQt4 import QtCore, QtGui, QtSql
from ui_settings import Ui_Settings
from ui_login import Ui_Login
from ui_import import Ui_Import
import enum
import utils
from database import db, DatabaseNotInitialisedException, ConnectionException
from delegates import AccountDelegate
from models import AccountEditModel, ImportModel

import csv

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
	# csv.py doesn't do Unicode; encode temporarily as UTF-8:
	csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
						dialect=dialect, **kwargs)
	for row in csv_reader:
		# decode UTF-8 back to Unicode, cell by cell:
		yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
	for line in unicode_csv_data:
		yield line.encode('utf-8')

class UserCancelledException(Exception):
	""" Exception to indicate user has cancelled the current operation
	"""

class DecoderError(Exception):
	""" General Decoder exceptions
	"""

class ImportDialog(Ui_Import, QtGui.QDialog):
	def __init__(self, files, parent=None):
		super(ImportDialog, self).__init__(parent=parent)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.setupUi(self)
		self.__rawData = {}
		self.__importInProgress = False
		self.__cancelImport = False
		self.__accountsModel = None

		self.progressBar.setVisible(False)

		accountModel = QtSql.QSqlTableModel(self)
		accountModel.setTable('accounttypes')
		accountModel.select()

		self.accountTypeComboBox.setModel(accountModel)
		self.accountTypeComboBox.setModelColumn(enum.kAccountTypeColumn_AccountName)
		self.accountTypeComboBox.setCurrentIndex(-1)

		self.__accountsModel = accountModel

		model = QtGui.QStandardItemModel()

		for filename in files:
			csvfile = QtCore.QFile(filename)

			if not csvfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
				raise Exception('Cannot open file %r' % filename)

			while not csvfile.atEnd():
				rawdata = csvfile.readLine().trimmed()
				dataDict = self.__rawData.setdefault(filename, [])
				dataDict.append(rawdata)

				row =  unicode_csv_reader([rawdata.data().decode('utf8')]).next()
				items = [QtGui.QStandardItem(item) for item in row]
				model.appendRow(items)

		self.importCancelButton.setEnabled(False)
		self.selectAllButton.setEnabled(False)

		self.view.setModel(model)
		self.view.resizeColumnsToContents()

		self.accountTypeComboBox.currentIndexChanged.connect(self.setAccountType)
		self.importCancelButton.clicked.connect(self.__importCancelPressed)
		self.selectAllButton.clicked.connect(self.view.selectAll)
		self.closeButton.clicked.connect(self.__close)

	def setAccountType(self, index):
		""" Account selection has changed

			Get settings for the account and create new model to decode the data
		"""
		dateField = self.__accountsModel.index(index, enum.kAccountTypeColumn_DateField).data().toPyObject()
		descriptionField = self.__accountsModel.index(index, enum.kAccountTypeColumn_DescriptionField).data().toPyObject()
		creditField = self.__accountsModel.index(index, enum.kAccountTypeColumn_CreditField).data().toPyObject()
		debitField = self.__accountsModel.index(index, enum.kAccountTypeColumn_DebitField).data().toPyObject()
		currencySign = self.__accountsModel.index(index, enum.kAccountTypeColumn_CurrencySign).data().toPyObject()
		dateFormat = self.__accountsModel.index(index, enum.kAccountTypeColumn_DateFormat).data().toString()

		model = ImportModel(self)
		db.commit.connect(model.save)
		db.rollback.connect(model.reset)

		with utils.showWaitCursor():
			records = self.__processRecords(dateField, descriptionField, creditField, debitField, currencySign, dateFormat)
			model.loadRecords(records)

			proxy = QtGui.QSortFilterProxyModel(model)
			proxy.setSourceModel(model)
			proxy.setFilterKeyColumn(0)

			self.view.setModel(proxy)
			self.view.verticalHeader().hide()
			self.view.setSortingEnabled(True)
			self.view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
			self.view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
			self.view.horizontalHeader().setStretchLastSection(True)
			self.view.sortByColumn(0, QtCore.Qt.AscendingOrder)
			self.view.resizeColumnsToContents()
			self.view.selectionModel().selectionChanged.connect(self.__recordsSelected)
			self.importCancelButton.setEnabled(False)
			self.selectAllButton.setEnabled(bool(model.numRecordsToImport()))
			self.__setCounters()

		# Hide txDate colum if we don't need it
		for row in xrange(model.rowCount()):
			if model.index(row, enum.kImportColumn_TxDate).data().isValid():
				self.view.setColumnHidden(enum.kImportColumn_TxDate, False)
				break
		else:
			self.view.setColumnHidden(enum.kImportColumn_TxDate, True)

	def __processRecords(self, dateIdx, descriptionIdx, creditIdx, debitIdx, currencySign, dateFormat):
		""" Generator to decode the raw csv data according to the account configuration.
			Yields record containing verified data ready to be saved to database
		"""

		for filename, rawRecords in self.__rawData.iteritems():
			for lineno, rawdata in enumerate(rawRecords):

				if not rawdata:
					continue

				dateField = descField = txDate = debitField = creditField = None
				row = unicode_csv_reader([rawdata.data().decode('utf8')]).next()

				try:
					if max(dateIdx, descriptionIdx, creditIdx, debitIdx) > len(row) -1:
						raise DecoderError('Bad record')

					dateField  = self.__getDateField(row[dateIdx], dateFormat)
					descField  = row[descriptionIdx]
					txDate     = self.__getTransactionDate(row[descriptionIdx], dateField)

					if debitIdx == creditIdx:
						amount = self.__getAmountField(row[debitIdx])
						if amount is not None:
							# Use currency multiplier to ensure that credit is +ve (money in),
							# debit -ve (money out)
							amount *= currencySign

							if amount > 0.0:
								creditField = amount
							else:
								debitField = amount
					else:
						debitField = self.__getAmountField(row[debitIdx])
						creditField = self.__getAmountField(row[creditIdx])
						debitField = abs(debitField) * -1.0 if debitField else None
						creditField = abs(creditField) if creditField else None

					if not debitField and not creditField:
						raise DecoderError('No credit or debit found')

				except DecoderError, exc:
					error = '%s[%d]: %r' % (QtCore.QFileInfo(filename).fileName(), lineno, str(exc))
					yield (rawdata, dateField, descField, txDate, debitField, creditField, error,)

				except Exception, exc:
					QtGui.QMessageBox.critical(
						self, 'Import Error', str(exc),
						QtGui.QMessageBox.Ok)

				else:
					yield (rawdata, dateField, descField, txDate, debitField, creditField, None,)

	def __getDateField(self, field, dateFormat):
		""" Extract date field using supplied format 
		"""
		date = QtCore.QDate.fromString(field, dateFormat)

		if not date.isValid():
			raise DecoderError('Invalid date: %r' % field)

		return date

	def __getTransactionDate(self, field, dateField):
		""" Try and extract a transaction date from the description field.
			Value format are ddMMMyy hhmm, ddMMMyy and ddMMM. 
			When the year is not available (or 2 digits) then the value validated date field
			is used
		"""
		timeDate = None

		#Format is "23DEC09 1210"
		rx = QtCore.QRegExp('(\\d\\d[A-Z]{3}\\d\\d \\d{4})')
		if rx.indexIn(field) != -1:
			timeDate = QtCore.QDateTime.fromString (rx.cap(1), "ddMMMyy hhmm").addYears(100)

		if timeDate is None:
			# Format is "06NOV10"
			rx = QtCore.QRegExp('(\\d{2}[A-Z]{3}\\d{2})')
			if rx.indexIn(field) != -1:
				timeDate = QtCore.QDateTime.fromString (rx.cap(1), "ddMMMyy").addYears(100)

		# Format is " 06NOV" <- note the stupid leading blank space..
		if timeDate is None:
			rx = QtCore.QRegExp(' (\\d\\d[A-Z]{3})')
			if rx.indexIn(field) != -1:
				# Add the year from date field to the transaction date
				timeDate = QtCore.QDateTime.fromString (rx.cap(1) + dateField.toString("yyyy"), "ddMMMyyyy")

		if timeDate is not None and timeDate.isValid():
			return timeDate

	def __getAmountField(self, field):
		""" Extract and return amount (double). If a simple conversion doesn't
			succeed, then try and parse the string to remove any currency sign
			or other junk.

			Returns None if field does not contain valid double.
		"""

		# Get rid of commas from amount field and try and covert to double
		field = field.replace(',', '')
		value, ok = QtCore.QVariant(field).toDouble()

		if not ok:
			# Probably has currency sign - extract all valid currency characters
			match = re.search('([\d\-\.]+)', field)
			if match:
				value, ok = QtCore.QVariant(match.group(1)).toDouble()

		if ok:
			return value

		return None

	def __importCancelPressed(self):
		if self.__importInProgress:
			self.__cancelImport = True
		else:
			self.__importRecords()

	def __setCounters(self):
		model = self.view.model().sourceModel()
		self.errorsCounter.setNum(model.numBadRecords())
		self.importedCounter.setNum(model.numRecordsImported())
		self.toImportCounter.setNum(model.numRecordsToImport())

	def __recordsSelected(self):
		""" Enable button cancel when we have selection
		"""
		numSelected = len(self.view.selectionModel().selectedRows())
		self.selectedCounter.setNum(numSelected)
		self.importCancelButton.setEnabled(bool(numSelected))

	def __close(self):
		""" Exit with bool value to indicate if data was saved,
			but not if it's our initial model
		"""
		model = self.view.model()

		if isinstance(model, QtGui.QStandardItemModel):
			self.done(0)
		else:
			self.done(self.view.model().sourceModel().dataSaved)

	def __importRecords(self):
		""" Import selected rows to database
		"""
		index = self.accountTypeComboBox.currentIndex()
		accountId = self.__accountsModel.index(index, enum.kAccountTypeColumn_AccountTypeId).data().toPyObject()
		selectionModel = self.view.selectionModel()
		indexes = selectionModel.selectedRows()

		if len(indexes) == 0:
			return

		try:
			self.progressBar.setVisible(True)

			proxyModel = self.view.model()
			dataModel = proxyModel.sourceModel()
			self.progressBar.setValue(0)
			self.progressBar.setMaximum(len(indexes))
			self.view.clearSelection()

			self.__importInProgress = True
			self.closeButton.setEnabled(False)
			self.selectAllButton.setEnabled(False)
			self.importCancelButton.setText('Cancel')
			self.importCancelButton.setEnabled(True)

			# Wrap the import in a transaction
			with db.transaction():
				for num, index in enumerate(indexes, 1):
					dataModel.saveRecord(accountId, proxyModel.mapToSource(index))
					self.view.scrollTo(index, QtGui.QAbstractItemView.EnsureVisible)
					self.view.resizeColumnsToContents()
					self.__setCounters()
					QtCore.QCoreApplication.processEvents()
					self.progressBar.setValue(self.progressBar.value() +1)

					if self.__cancelImport:
						raise UserCancelledException

				if num:
					if QtGui.QMessageBox.question(
						self, 'Import', 'Imported %d records successfully' % num,
						QtGui.QMessageBox.Save|QtGui.QMessageBox.Cancel) != QtGui.QMessageBox.Save:
						# By raising here we will rollback the database transaction
						raise UserCancelledException

		except UserCancelledException:
			dataModel.reset()

		except Exception, exc:
			QtGui.QMessageBox.critical(self, 'Import Error', str(exc), QtGui.QMessageBox.Ok)

		finally:
			self.__cancelImport = False
			self.__importInProgress = False
			self.closeButton.setEnabled(True)
			self.importCancelButton.setText('Import')
			self.progressBar.setVisible(False)

			canImport = bool(dataModel.numRecordsToImport())
			self.importCancelButton.setEnabled(canImport)
			self.selectAllButton.setEnabled(canImport)


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

		self.enableCommit(False)

		model = AccountEditModel(self)
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
		self.view.setItemDelegate(AccountDelegate(self))

		model.dataChanged.connect(self.view.clearSelection)
		model.dataChanged.connect(self.__dataChanged)
		model.beforeInsert.connect(self.validateNewAccount)

		self.model = model

	def __dataChanged(self, left, right):
		self.enableCommit(True)

	def validateNewAccount(self, record):
		try:
			if record.value(enum.kAccountTypeColumn_AccountName).toString().isEmpty():
				raise Exception('Account name cannot be empty')

			value, ok = record.value(enum.kAccountTypeColumn_DateField).toInt()
			if not ok or value < 0:
				raise Exception('Date field must be set (index of date field)')

			value, ok = record.value(enum.kAccountTypeColumn_CreditField).toInt()
			if not ok or value < 0:
				raise Exception('Credit field must be set (index of credit field)')

			value, ok = record.value(enum.kAccountTypeColumn_DebitField).toInt()
			if not ok or value < 0:
				raise Exception('Debit field must be set (index of debit field)')

			if record.value(enum.kAccountTypeColumn_DescriptionField).toString().isEmpty():
				raise Exception('Description field must be set (index of description field)')

			value, ok = record.value(enum.kAccountTypeColumn_CurrencySign).toInt()
			if not ok or value not in (1, -1):
				raise Exception('Currency sign value must be 1 or -1')

			if record.value(enum.kAccountTypeColumn_DateFormat).toString().isEmpty():
				raise Exception('"Date format cannot be empty (eg "dd/MM/yyyy")')

		except Exception, err:
			QtGui.QMessageBox.critical(self, 'Account failed', str(err), QtGui.QMessageBox.Ok)
			# Trash the bad record
			record.clear()

	def saveSettings(self):

		if not self.model.submitAll() and self.model.lastError().isValid():
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

		for column in xrange(1, self.model.columnCount()):
			index = self.model.index(rowCount, column)
			self.model.setData(index, QtCore.QVariant(), QtCore.Qt.EditRole)

		index = self.model.index(rowCount, enum.kAccountTypeColumn_AccountName)
		self.view.setCurrentIndex(index)
		self.view.edit(index)

	def deleteAccount(self):
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
		self.closeButton.clicked.connect(self.reject)

		self.hostnameEdit.setText(db.hostname)
		self.databaseEdit.setText(db.database)
		self.usernameEdit.setText(db.username)
		self.passwordEdit.setText(db.password)
		self.portSpinBox.setValue(db.port)

	def activateConnection(self):
		db.database = self.databaseEdit.text()
		db.hostname = self.hostnameEdit.text()
		db.username = self.usernameEdit.text()
		db.password = self.passwordEdit.text()
		db.port = self.portSpinBox.value()

		try:
			with utils.showWaitCursor():
				db.connect()
		except DatabaseNotInitialisedException:
			if QtGui.QMessageBox.question(
					self, 'Database', 
					'Database %s is empty, do you want to initialise it?' % db.database, 
					QtGui.QMessageBox.Yes|QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
				try:
					db.initialise()
				except ConnectionException, err:
					QtGui.QMessageBox.critical(self, 'Database ', str(err))
				else:
					QtGui.QMessageBox.information(self, 'Database', 'Database initialised successfully')
			else:
				return
		except ConnectionException, err:
			QtGui.QMessageBox.warning(self, 'Database', 'Failed to connect: %s' % str(err))
		else:
			self.accept()
