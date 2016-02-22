from PySide import QtGui, QtCore
from pydosh import enum

class AccountDelegate(QtGui.QItemDelegate):
	def __init__(self, parent=None):
		super(AccountDelegate, self).__init__(parent=parent)

	def createEditor(self, parent, option, index):
		lineEdit = QtGui.QLineEdit(parent=parent)
		pattern = None

		if index.column() in (
				enum.kAccountType__DateField,
				enum.kAccountType__DescriptionField,
				enum.kAccountType__CreditField,
				enum.kAccountType__DebitField):
			pattern = QtCore.QRegExp('[0-9]+')

		elif index.column() == enum.kAccountType__DateFormat:
			pattern = QtCore.QRegExp('[dMy/ ]+')

		elif index.column() == enum.kAccountType__CurrencySign:
			pattern = QtCore.QRegExp('-1|1')

		if pattern:
			lineEdit.setValidator(QtGui.QRegExpValidator(pattern))

		return lineEdit

	def setModelData(self, editor, model, index):

		if not index.isValid():
			return

		if editor:
			model.setData(index, editor.text())

	def updateEditorGeometry(self, editor, option, index):
		editor.setGeometry(option.rect)
