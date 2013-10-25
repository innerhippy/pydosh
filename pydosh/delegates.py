from PySide import QtGui, QtCore
import enum

class AccountDelegate(QtGui.QItemDelegate):
	def __init__(self, parent=None):
		super(AccountDelegate, self).__init__(parent=parent)

	def createEditor(self, parent, option, index):
		lineEdit = QtGui.QLineEdit(parent=parent)
		pattern = None

		if index.column() in (
						enum.kAccountTypeColumn_DateField,
						enum.kAccountTypeColumn_DescriptionField,
						enum.kAccountTypeColumn_CreditField,
						enum.kAccountTypeColumn_DebitField):
			pattern = QtCore.QRegExp('[0-9]+')

		elif index.column() == enum.kAccountTypeColumn_DateFormat:
			pattern = QtCore.QRegExp('[dMy/]+')

		elif index.column() == enum.kAccountTypeColumn_CurrencySign:
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
