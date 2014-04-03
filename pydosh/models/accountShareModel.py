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
		self.select()

		model = QtSql.QSqlRelationalTableModel(self)
		model.setTable('accountshare')
		model.setRelation(enum.kAccountShare_UserId, QtSql.QSqlRelation('users', 'userid', 'username'))
		model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
		model.select()
		self.accountShareModel = model
		self.accountId = None

	def submitAll(self):
		status = self.accountShareModel.submitAll()
		if not status and self.accountShareModel.lastError().isValid():
			print self.accountShareModel.query().lastQuery()
			raise Exception(self.accountShareModel.lastError().text())

	def accountChanged(self, accountId):
		self.accountId = accountId
		self.accountShareModel.setFilter(
			'accountshare.accountid=%s AND accountshare.userid != %s' %
			(self.accountId, db.userId)
		)
#		self.sharedWith = [
#			self.accountShareModel.index(row, enum.kAccountShare_UserId).data()
#				for row in xrange(self.accountShareModel.rowCount())
#		]
		self.reset()

	def flags(self, index):
#		flags = super(AccountShareModel, self).flags(index)
		return QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled

	def data(self, item, role=QtCore.Qt.DisplayRole):
		if not item.isValid():
			return None

		if role == QtCore.Qt.CheckStateRole:
			sharedWith = [
				self.accountShareModel.index(row, enum.kAccountShare_UserId).data()
					for row in xrange(self.accountShareModel.rowCount())
			]
			if self.index(item.row(), enum.kUsers_UserName).data() in sharedWith:
				return QtCore.Qt.Checked
			else:
				return QtCore.Qt.Unchecked
#		if role == QtCore.Qt.ForegroundRole and self.isDirty(item):
#			return QtGui.QColor(255, 165, 0)

		return super(AccountShareModel, self).data(item, role)

	def setData(self, index, value, role=QtCore.Qt.EditRole):
		""" Change the account share values
		"""
		if role == QtCore.Qt.CheckStateRole:
			if value == QtCore.Qt.Unchecked:
				# Share has been de-selected.
				match = self.accountShareModel.match(
					self.accountShareModel.index(0, enum.kAccountShare_UserId),
					QtCore.Qt.DisplayRole,
					index.data(QtCore.Qt.DisplayRole)
				)
				assert len(match) == 1, 'Expecting to find match in account shares'
				status = self.accountShareModel.removeRow(match[0].row())
			else:
				rowCount = self.accountShareModel.rowCount()
				userId = self.index(index.row(), enum.kUsers_UserId).data()
				self.accountShareModel.insertRow(rowCount)
				status = (
					self.accountShareModel.setData(
						self.accountShareModel.index(rowCount, 1),self.accountId) and
					self.accountShareModel.setData(
						self.accountShareModel.index(rowCount, 2), userId)
				)

			self.dataChanged.emit(index, index)
			return status

		return False

