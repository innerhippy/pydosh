from PyQt4 import QtGui, QtCore
import enum

class AccountDelegate(QtGui.QItemDelegate):
	def __init__(self, parent=None):
		super(AccountDelegate, self).__init__(parent=parent)

	def createEditor(self, parent, option, index):

		lineEdit = QtGui.QLineEdit(parent=parent)

		if index.column() in (
						enum.kAccountTypeColumn_DateField,
						enum.kAccountTypeColumn_DescriptionField,
						enum.kAccountTypeColumn_CreditField,
						enum.kAccountTypeColumn_DebitField):
			lineEdit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp('[0-9]+'), lineEdit))

		elif index.column() == enum.kAccountTypeColumn_CurrencySign:
			lineEdit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp('-1|1')))

		return lineEdit

	def setModelData(self, editor, model, index):

		if not index.isValid():
			return

		if editor:
			model.setData(index, editor.text())

	def updateEditorGeometry(self, editor, option, index):
		editor.setGeometry(option.rect)
