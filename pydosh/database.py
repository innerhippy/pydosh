from PyQt4 import QtCore, QtSql


class _Database(QtCore.QObject):
	def __init__(self):
		super(_Database, self).__init__()
		db = QtSql.QSqlDatabase.addDatabase("QPSQL")
		#db = QtSql.QSqlDatabase.addDatabase("QMYSQL")
		db.setDatabaseName('doshlogger2')
		db.setHostName('xambo')
		#db.setHostName('127.0.0.1')
		db.setUserName('will')
#		db.setPort(5432)
		#db.setPort(3306)

		db.open()

#		import pdb
#		pdb.set_trace()

	@property
	def userId(self):
		return 2

	@property
	def isConnected(self):
		""" A rather ugly way to see if we are connected to the database
		"""
		names = QtSql.QSqlDatabase.connectionNames()
		return len(names) and QtSql.QSqlDatabase.database(names[0], False).isOpen()

db = _Database()
