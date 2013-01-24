import pdb
from PyQt4 import QtCore, QtGui, QtSql
from contextlib  import contextmanager


class _Database(QtCore.QObject):
	connected = QtCore.pyqtSignal(bool)

	def __init__(self):
		super(_Database, self).__init__()
		self.__userId = None

	@property
	def driver(self):
		settings = QtCore.QSettings()
		return settings.value('options/driver', 'QPSQL').toString()

	@driver.setter
	def driver(self, driver):
		if driver != self.driver:
			settings = QtCore.QSettings()
			settings.setValue('options/driver', driver)

	@property
	def hostname(self):
		settings = QtCore.QSettings()
		return settings.value('options/hostname', 'localhost').toString()

	@hostname.setter
	def hostname(self, hostname):
		if hostname != self.hostname:
			settings = QtCore.QSettings()
			settings.setValue('options/hostname', hostname)

	@property
	def database(self):
		settings = QtCore.QSettings()
		return settings.value('options/database', 'doshlogger2').toString()

	@database.setter
	def database(self, database):
		if database != self.database:
			settings = QtCore.QSettings()
			settings.setValue('options/database', database)

	@property
	def username(self):
		settings = QtCore.QSettings()
		return settings.value('options/username').toString()

	@username.setter
	def username(self, username):
		if username != self.username:
			settings = QtCore.QSettings()
			settings.setValue('options/username', username)

	@property
	def password(self):
		settings = QtCore.QSettings()
		return settings.value('options/password').toString()

	@password.setter
	def password(self, password):
		if password != self.password:
			settings = QtCore.QSettings()
			settings.setValue('options/password', password)

	@property
	def port(self):
		settings = QtCore.QSettings()
		port, ok = settings.value('options/port', 3306).toInt()
		if ok:
			return port

	@port.setter
	def port(self, port):
		if port != self.port:
			settings = QtCore.QSettings()
			settings.setValue('options/port', port)

	@property
	def userId(self):
		""" Return the cached value or get from database if not set yet
		"""

		if self.__userId is None and self.isConnected:
			query=QtSql.QSqlQuery()
			query.prepare('SELECT userid from users where username=(?)')
			query.addBindValue(self.username)
			query.exec_()
			query.next()

			if query.lastError().isValid():
				raise Exception(query.lastError().text())

			self.__userId, ok = query.value(0).toInt()

			if not ok:
				raise Exception('Cannot find userid for %r' % self.username)

		return self.__userId

	@property
	def isConnected(self):
		""" A rather ugly way to see if we are connected to the database
		"""
		names = QtSql.QSqlDatabase.connectionNames()
		return len(names) and QtSql.QSqlDatabase.database(names[0], False).isOpen()

	def disconnect(self):
		for name in QtSql.QSqlDatabase.connectionNames():
			QtSql.QSqlDatabase.removeDatabase(name)

		self.__userId = None
		self.connected.emit(False)

	def connect(self):
		self.disconnect()

		db = QtSql.QSqlDatabase.addDatabase(self.driver)
		db.setDatabaseName(self.database)
		db.setHostName(self.hostname)
		db.setUserName(self.username)
		db.setPassword(self.password)
		db.setPort(self.port)

		if not db.open():
			QtGui.QMessageBox.warning(None, 'Connection failed', 'Failed to connect to database: %s' % db.lastError().text())
			return False

		self.connected.emit(self.isConnected)
		return True

	@contextmanager
	def transaction(self):
		""" Context manager to provide transaction code blocks. Any exception
			raised in the 'with' block will cause a rollback. Otherwise commit.
		"""

		try:
		#	print 'Start transaction'
			QtSql.QSqlDatabase.database().transaction()
			yield
		except:
		#	print 'Rollback'
			QtSql.QSqlDatabase.database().rollback()
			raise
		else:
		#	print 'Commit transaction'
			QtSql.QSqlDatabase.database().commit()

db = _Database()

