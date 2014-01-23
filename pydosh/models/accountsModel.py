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


class AccountEditModel(QtSql.QSqlTableModel):
	def __init__(self, parent=None):
		super(AccountEditModel, self).__init__(parent=parent)

	def data(self, item, role=QtCore.Qt.DisplayRole):
		if not item.isValid():
			return None

		if role == QtCore.Qt.ForegroundRole and self.isDirty(item):
			return QtGui.QColor(255, 165, 0)

		return super(AccountEditModel, self).data(item, role)

	def setData(self, index, value, role=QtCore.Qt.EditRole):
		# Don't flag cell as changed when it hasn't
		if role == QtCore.Qt.EditRole and index.data(QtCore.Qt.DisplayRole) == value:
			return False

		return super(AccountEditModel, self).setData(index, value, role)

	def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):

		if role == QtCore.Qt.DisplayRole:
			if section == enum.kAccountTypeColumn_AccountName:
				return 'Account Name'
			elif section == enum.kAccountTypeColumn_DateField:
				return 'Date'
			elif section == enum.kAccountTypeColumn_DescriptionField:
				return 'Description'
			elif section == enum.kAccountTypeColumn_CreditField:
				return 'Credit'
			elif section == enum.kAccountTypeColumn_DebitField:
				return 'Debit'
			elif section == enum.kAccountTypeColumn_CurrencySign:
				return 'Currency sign'
			elif section == enum.kAccountTypeColumn_DateFormat:
				return 'Date formats'

		return None

