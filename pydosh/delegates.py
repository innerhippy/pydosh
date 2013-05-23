from PyQt4 import QtGui, QtCore
import enum

class RecordStyleDelegate(QtGui.QStyledItemDelegate):
	def __init__(self, view, parent=None):
		super(RecordStyleDelegate, self).__init__(parent=parent)
		self._view = view

	def paint(self, painter, option, index):
		print option.state
		if index.column() == enum.kRecordColumn_Amount:
			if index.data(QtCore.Qt.UserRole).toPyObject() > 0.0:
				painter.fillRect(option.rect, option.palette.highlight())
				painter.setPen(self._view.creditColour)
			else:
				painter.setPen(self._view.debitColour)
			#option.font.setWeight(QtGui.QFont.Bold)
		super(RecordStyleDelegate, self).paint(painter, option, index)

	def noinitStyleOption(self, option, index):
		# let the base class initStyleOption fill option with the default values
		super(RecordStyleDelegate,self).initStyleOption(option, index)
		# override what you need to change in option
		#if option.state & QtGui.QStyle.State_Selected:
		#	option.state &= ~ QtGui.QStyle.State_Selected
		#option.backgroundBrush = QtGui.QBrush(QtGui.QColor(100, 200, 100, 200))
		#print option.palette.alternateBase().color().red(), option.palette.window().color().red()
		if index.column() == enum.kRecordColumn_Amount:
			if index.data(QtCore.Qt.UserRole).toPyObject() > 0.0:
				option.backgroundBrush = self._view.creditColour
			else:
				option.backgroundBrush = self._view.debitColour

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
