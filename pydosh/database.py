from PyQt4 import QtCore, QtSql


class _Database(QtCore.QObject):
	def __init__(self):
		super(_Database, self).__init__()
		db = QtSql.QSqlDatabase.addDatabase("QPSQL")
		db.setDatabaseName('doshlogger2')
		db.setHostName('xambo')
		db.setUserName('will')
		db.setPort(5432)

		db.open()

#		import pdb
#		pdb.set_trace()

	@property
	def userId(self):
		return 2

db = _Database()
