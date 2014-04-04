import re
import os
import csv
import hashlib
import codecs
from PySide import QtCore, QtGui, QtSql

from pydosh import enum
from pydosh import currency, utils
from pydosh.database import db
import pydosh.pydosh_rc

import pdb


class AccountShareModel(QtSql.QSqlTableModel):
	def __init__(self, parent=None):
		super(AccountShareModel, self).__init__(parent=parent)


		self.setTable('users')
		self.setFilter('userid != %s' % db.userId)
		self.setSort(enum.kUsers_UserName, QtCore.Qt.AscendingOrder)
		self.select()

		model = QtSql.QSqlRelationalTableModel(self)
		model.setTable('accountshare')
		model.setRelation(
			enum.kAccountShare_UserId, 
			QtSql.QSqlRelation('users', 'userid', 'username')
		)
		model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
		model.select()
		self.shareModel = model
		self.accountId = None

	def submitAll(self):
		status = self.shareModel.submitAll()
		if not status and self.shareModel.lastError().isValid():
			raise Exception(self.shareModel.lastError().text())
		return status

	def accountChanged(self, accountId):
#		pdb.set_trace()
		self.accountId = accountId
		self.shareModel.setFilter(
			'accountshare.accountid=%s AND accountshare.userid != %s' %
			(self.accountId, db.userId)
		)
#		self.sharedWith = [
#			self.shareModel.index(row, enum.kAccountShare_UserId).data()
#				for row in xrange(self.shareModel.rowCount())
#		]
		#self.select()

	def flags(self, index):
		return QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled

	def data(self, item, role=QtCore.Qt.DisplayRole):
		if not item.isValid():
			return None

		if role == QtCore.Qt.CheckStateRole:
			print self.shareModel.query().lastQuery()
			sharedWith = [
				self.shareModel.index(row, enum.kAccountShare_UserId).data()
					for row in xrange(self.shareModel.rowCount())
			]
			if self.index(item.row(), enum.kUsers_UserName).data() in sharedWith:
				print 'checked', sharedWith, self.shareModel.rowCount()
				return QtCore.Qt.Checked
			else:
				print 'unchecked', sharedWith, self.shareModel.rowCount()
				return QtCore.Qt.Unchecked

		return super(AccountShareModel, self).data(item, role)

	def setData(self, index, value, role=QtCore.Qt.EditRole):
		""" Change the account share values
		"""
		if role == QtCore.Qt.CheckStateRole:
			if value == QtCore.Qt.Unchecked:
				# Share has been de-selected.
				match = self.shareModel.match(
					self.shareModel.index(0, enum.kAccountShare_UserId),
					QtCore.Qt.DisplayRole,
					index.data(QtCore.Qt.DisplayRole)
				)
				assert len(match) == 1, 'Expecting to find match in account shares'
				status = self.shareModel.removeRow(match[0].row())
			else:
				rowCount = self.shareModel.rowCount()
				userId = self.index(index.row(), enum.kUsers_UserId).data()
				self.shareModel.insertRow(rowCount)
				status = (
					self.shareModel.setData(
						self.shareModel.index(rowCount, 1),self.accountId) and
					self.shareModel.setData(
						self.shareModel.index(rowCount, 2), userId)
				)

			self.dataChanged.emit(index, index)
			return status

		return False

