from PyQt4 import QtCore, QtSql
from contextlib  import contextmanager
import pydosh_rc

class ConnectionException(Exception):
	""" Connection exception
	"""

class DatabaseNotInitialisedException(Exception):
	""" Exception raised if database is empty
	"""

class _Database(QtCore.QObject):
	commit = QtCore.pyqtSignal()
	rollback = QtCore.pyqtSignal()

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
		return settings.value('options/database', 'pydosh').toString()

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
		port, ok = settings.value('options/port', 5432).toInt()
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
		if self.__userId is None:# and self.isConnected:
			self.__userId = self.__getCurrentUserId()

		return self.__userId

	def initialise(self):
		if self. __isDatabaseInitialised():
			raise ConnectionException('Database is already initialised')

		with self.transaction():
			self.__runCommandsFromFile(":/schema/schema.sql")
			self.__runCommandsFromFile(":/schema/accounttypes_data.sql")

	@contextmanager
	def transaction(self):
		""" Context manager to provide transaction code blocks. Any exception
			raised in the 'with' block will cause a rollback. Otherwise commit.
		"""
		try:
			QtSql.QSqlDatabase.database().transaction()
			yield
		except:
			#print 'Rollback'
			QtSql.QSqlDatabase.database().rollback()
			self.rollback.emit()
			raise
		else:
			#print 'Commit transaction'
			QtSql.QSqlDatabase.database().commit()
			self.commit.emit()

	def connect(self):
		db = QtSql.QSqlDatabase.addDatabase(self.driver)
		db.setDatabaseName(self.database)
		db.setHostName(self.hostname)
		db.setUserName(self.username)
		db.setPassword(self.password)
		db.setPort(self.port)

		if not db.open():
			raise ConnectionException('Failed to connect to database:\n%s' % db.lastError().text())

		if not self.__isDatabaseInitialised():
			raise DatabaseNotInitialisedException

	def __getCurrentUserId(self):
		""" Returns the current username's userid from the users table.
			Raises ConnectionException if cannot be found
		"""
		query=QtSql.QSqlQuery()
		query.prepare('SELECT userid from users where username=(?)')
		query.addBindValue(self.username)
		query.exec_()
		query.next()

		if query.lastError().isValid():
			raise ConnectionException(query.lastError().text())

		if not query.isValid():
			# no user exists - create entry for current user
			return self.__addCurrentUser()

		userId, ok = query.value(0).toInt()

		if not ok:
			raise ConnectionException('Cannot get userid for %s' % self.username)

		return userId

	def __addCurrentUser(self):
		""" Add the current user to the users table.
			Returns new user id
		"""
		query = QtSql.QSqlQuery()
		query.prepare('INSERT INTO users (username) VALUES (?) RETURNING userid')
		query.addBindValue(self.username)
		query.exec_()

		if query.lastError().isValid():
			raise ConnectionException(query.lastError().text())

		query.next()
		userId, ok = query.value(0).toInt()

		if not ok:
			raise ConnectionException('Cannot add new user %s' % self.username)

		return userId

	def __runCommandsFromFile(self, filename):

		cmdfile = QtCore.QFile(filename)

		if not cmdfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
			raise ConnectionException('Cannot open command file %s' % filename)

		stream = QtCore.QTextStream(cmdfile)

		# commands in file can span multiple lines. Read everything in 
		# a buffer then run each command, delimited by ';'
		buff = []

		while not stream.atEnd():
			line = stream.readLine()

			if len(line) == 0 or line.startsWith('--'):
				continue

			buff.append(str(line))

		# combine all command and then split again on ';'
		for command in ' '.join(buff).split(';'):
			self.__executeQuery(command.strip())


	def __executeQuery(self, query):
		sql = QtSql.QSqlQuery(query)
		if sql.lastError().isValid():
			raise ConnectionException('Failed to run command %s:\n%s' % (query, sql.lastError().text()))

	def __isDatabaseInitialised(self):
		query = QtSql.QSqlQuery()

		query.prepare("""
			SELECT count(table_name)
			FROM information_schema.tables
			WHERE table_schema = 'public'
			AND table_catalog=?
		""")

		query.addBindValue(self.database)
		query.exec_()

		if query.lastError().isValid():
			raise ConnectionException(query.lastError().text())

		query.next()
		count, ok = query.value(0).toInt()

		if not ok:
			raise ConnectionException('Failed to run command %s' % query.lastQuery())

		return count > 0

db = _Database()

