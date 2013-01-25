from PyQt4 import QtCore, QtGui
QtCore.pyqtRemoveInputHook()

import pdb

class SearchComboBox(QtGui.QComboBox):
	""" Extension of QComboBox to enable search and auto-completion
	"""
	def __init__(self, parent=None):
		super( SearchComboBox, self ).__init__(parent)
		self.__editText = ''
		self.setEditable(True)

		self.proxyModel = QtGui.QSortFilterProxyModel(self)
		self.proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.proxyModel.setSourceModel(self.model())

		self.completer = QtGui.QCompleter(self.proxyModel, self)
		self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
		self.setCompleter(self.completer)

		self.lineEdit().textEdited[unicode].connect(self.proxyModel.setFilterFixedString)
		self.completer.activated.connect(self.__completerActivated)


	def setEditText(self, text):
		""" Intercept setEditText to persist value. 
			The field is cleared when the QLineEdit gets focus and is restored when it looses focus.
			Set the initial palette colour to red
		"""
		self.__editText = text
		super(SearchComboBox, self).setEditText(text)
		palette = QtGui.QPalette()
		palette.setColor(QtGui.QPalette.Text, QtCore.Qt.red)
		self.lineEdit().setPalette(palette)

	def selectionValid(self):
		return self.findText(self.currentText()) != -1

	def focusInEvent(self, event):
		""" Clear QLineEdit field and set palette back to default value
		"""
		if self.currentText() == self.__editText:
			palette = QtGui.QPalette()
			self.lineEdit().setPalette(palette)
			super(SearchComboBox,self).setEditText('')
		super(SearchComboBox, self).focusInEvent(event)

	def focusOutEvent(self, event):
		""" Reset QLineEdit field if we don't have a valid selection
		"""
		if not self.selectionValid():
			self.setEditText(self.__editText)
		super(SearchComboBox, self).focusOutEvent(event)

	def view(self):
		return self.completer.popup()

	def __completerActivated(self, text):
		if text:
			index = self.findText(text)
			self.setCurrentIndex(index)

class CheckComboModel(QtGui.QStandardItemModel):
	
	checkStateChanged = QtCore.pyqtSignal()
	dataChanged = QtCore.pyqtSignal('QModelIndex, QModelIndex)')

	def __init__(self, parent=None):
		super(CheckComboModel, self).__init__(0, 1, parent=parent)

	def flags(self, index):
		return super(CheckComboModel, self).flags(index) | QtCore.Qt.ItemIsUserCheckable


	def data(self, index, role):
		value = super(CheckComboModel, self).data(index, role)
		
		if index.isValid() and role == QtCore.Qt.CheckStateRole and not value.isValid():
			value = QtCore.Qt.Unchecked

		return value

	def setData(self, index, value, role):
		ok = super(CheckComboModel, self).setData(index, value, role)
		if ok and role == QtCore.Qt.CheckStateRole:
			self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
			self.emit(QtCore.SIGNAL('checkStateChanged()'))

		return ok

class MultiComboBox(QtGui.QComboBox):
	
	checkedItemsChanged = QtCore.pyqtSignal('PyQt_PyObject')
	
	def __init__(self, parent=None):
		super(MultiComboBox, self).__init__(parent=parent)
		
		self.setModel(CheckComboModel(self))
		self.connect(self, QtCore.SIGNAL('activated(int)'), self.__toggleCheckState)
		self.connect(self.model(), QtCore.SIGNAL('checkStateChanged()'), self.__updateCheckedItems)
		self.connect(self.model(), QtCore.SIGNAL('rowsInserted(QModelIndex, int, int)'), self.__updateCheckedItems)
		self.connect(self.model(), QtCore.SIGNAL('rowsRemoved(QModelIndex, int, int)'), self.__updateCheckedItems)

		lineEdit = QtGui.QLineEdit(self)
		lineEdit.setReadOnly(True)
		self.setLineEdit(lineEdit)
		#lineEdit.disconnect(self, QtCore.SIGNAL('textChanged(QString)'))
		self.setInsertPolicy(QtGui.QComboBox.NoInsert)
		
		self.view().installEventFilter(self)
		self.view().window().installEventFilter(self)
		self.view().viewport().installEventFilter(self)

		self.__defaultText = '...'
		self.__containerMousePress = False

	def eventFilter(self, receiver, event):

		if event.type() in (QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease):
			if receiver == self and event.key() in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
				self.showPopup()
				return True

			elif event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape):
				super(MultiComboBox, self).hidePopup()
				return True

		elif event.type() == QtCore.QEvent.MouseButtonPress:
			self.__containerMousePress = (receiver == self.view().window())

		elif event.type() == QtCore.QEvent.MouseButtonRelease:
			self.__containerMousePress = False
		
		return False

	def __toggleCheckState(self, index):
		value = self.itemData(index, QtCore.Qt.CheckStateRole)
		if value.isValid():
			state = value.toPyObject()
			self.setItemData(index, QtCore.Qt.Checked if state == QtCore.Qt.Unchecked else QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole) 

	def checkedItems(self):
		items = []
		if self.model():
			currentIndex = self.model().index(0, self.modelColumn(), self.rootModelIndex())
			indexes = self.model().match(currentIndex, QtCore.Qt.CheckStateRole, QtCore.Qt.Checked, -1, QtCore.Qt.MatchExactly)
			items = [index.data().toString() for index in indexes]
		return items

	def __updateCheckedItems(self, ):
		items = self.checkedItems()

		palette = QtGui.QPalette()
		if len(items) == 0:
			self.setEditText(self.__defaultText)
			palette.setColor(QtGui.QPalette.Text, QtCore.Qt.red)
		else:
			self.setEditText(', '.join([str(item) for item in items]))

		self.lineEdit().setPalette(palette)
		self.emit(QtCore.SIGNAL('checkedItemsChanged(PyQt_PyObject)'), items)

	def hidePopup(self):
		if self.__containerMousePress:
			super(MultiComboBox, self).hidePopup()
#
#	def itemCheckState(self, index):
#		return self.itemData(index, QtCore.Qt.CheckStateRole).toInt()
#	
#	def setItemCheckState(self, index, state):
#		self.setItemData(index, state, QtCore.Qt.CheckStateRole)
#
#	def setCheckedItems(self, items):
#		for text in items:
#			index = self.findText(text)
#			self.setItemCheckState(index, QtCore.Qt.Checked if index != -1 else QtCore.Qt.Unchecked)

	def setDefaultText(self, text):
		if text != self.__defaultText:
			self.__defaultText = text
			self.updateCheckedItems()


def main():
#	from mpc.pyqtUtils.utils import SignalTracer
#	tracer = SignalTracer()
	app = QtGui.QApplication(sys.argv)

	widget = MultiComboBox()
	#tracer.monitor(widget.lineEdit())

	widget.addItems(['item %d' %i for i in xrange(10)])

	dialog = QtGui.QDialog()
	layout = QtGui.QVBoxLayout()
	layout.addWidget(widget)

	dialog.setLayout(layout)
	dialog.show()

	app.exec_()
	return 0

	

if __name__ == '__main__':
	import sys
	sys.exit(main())


