from PyQt4 import QtCore, QtGui

from models import CheckComboModel

class MultiComboBox(QtGui.QComboBox):
	""" Extension of QComboBox widget that allows for multiple selection
	"""
	selectionChanged = QtCore.pyqtSignal()
	clearAll = QtCore.pyqtSignal()
	checkAll = QtCore.pyqtSignal()

	def __init__(self, parent=None):
		super(MultiComboBox, self).__init__(parent=parent)

		self._defaultText = ''
		self.__persistDropdown = False

		self.setLineEdit(QtGui.QLineEdit())
		self.setInsertPolicy(QtGui.QComboBox.NoInsert)

		self.view().installEventFilter(self)
		self.view().window().installEventFilter(self)
		self.view().viewport().installEventFilter(self)
		self.installEventFilter(self)

		self.setModel(CheckComboModel())
		self.activated[int].connect(self.__toggleCheckState)
		self.clearAll.connect(self._clearAllEvent)
		self.checkAll.connect(self._checkAllEvent)


	def __checkAll(self, check=False):
		""" Function to set all the items as checked or unchecked based on the argument.

			Args:
				check(bool):		check state
		"""
		searchState = QtCore.Qt.Unchecked if check else QtCore.Qt.Checked
		assignState = QtCore.Qt.Checked if check else QtCore.Qt.Unchecked 

		modelIndex = self.model().index(0, self.modelColumn(), self.rootModelIndex())
		modelIndexList = self.model().match(modelIndex, QtCore.Qt.CheckStateRole, searchState, -1, QtCore.Qt.MatchExactly)
		for index in modelIndexList:
			self.setItemData(index.row(), assignState, QtCore.Qt.CheckStateRole)

		self.__updateCheckedItems()

	def setLineEdit(self, edit):
		edit.setReadOnly(True)
		edit.installEventFilter(self)
		super(MultiComboBox, self).setLineEdit(edit)

	def setModel(self, model):
		super(MultiComboBox, self).setModel(model)
		model.checkStateChanged.connect(self.__updateCheckedItems)
		model.rowsInserted.connect(self.__updateCheckedItems)
		model.rowsRemoved.connect(self.__updateCheckedItems)

	def defaultText(self):
		""" Function to get the default text of ComboBox.

			 Returns:
				(str) return the default text.
		"""
		return self._defaultText

	def setDefaultText(self, text):
		""" Function to set the default text of ComboBox.

			Args:
				text (str): string for default text
		"""
		self._defaultText = text
		self.__updateCheckedItems()

	def eventFilter(self, receiver, event):
		if event.type() in (QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease):
			if receiver == self and event.key() in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
				self.showPopup()
				return True

			elif event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape):
				super(MultiComboBox, self).hidePopup()
				return True

		elif event.type() == QtCore.QEvent.MouseButtonPress:
			# Cancel the dropdown persist if we've clicked outside the widget
			if receiver == self.view().window():
				self.__persistDropdown = False

		return False

	def __toggleCheckState(self, index):
		# Can't seem to block signals from lineEdit, so do it the hard way...
		if self.sender() == self.lineEdit():
			return

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

	def checkedIndexes(self):
		indexes = []
		if self.model():
			currentIndex = self.model().index(0, self.modelColumn(), self.rootModelIndex())
			indexes = self.model().match(currentIndex, QtCore.Qt.CheckStateRole, QtCore.Qt.Checked, -1, QtCore.Qt.MatchExactly)
		return indexes

	def _clearAllEvent(self):
		""" Event for clear all check from the list view. 
		"""
		self.__checkAll(False)

	def _checkAllEvent(self):
		""" Event for check all from the list view. 
		"""
		self.__checkAll(True)

	def contextMenuEvent(self, event):
		""" Event for create context menu. 
			Args:
				event (QEvent):		mouse right click event.
		"""
		signalMap = {}
		contextMenu = QtGui.QMenu(self)

		clearAllAction = contextMenu.addAction("Clear All")
		signalMap[clearAllAction] = "clearAll()"
		checkAllAction = contextMenu.addAction("Check All")
		signalMap[checkAllAction] = "checkAll()"

		contextMenuAction = contextMenu.exec_(QtGui.QCursor.pos())
		if contextMenuAction and signalMap.has_key(contextMenuAction):
			self.emit(QtCore.SIGNAL(signalMap[contextMenuAction]))

	def __updateCheckedItems(self):
		items = self.checkedItems()

		if items:
			self.setEditText(', '.join([str(item) for item in items]))
		else:
			self.setEditText(self._defaultText)

		self.selectionChanged.emit()

	def showPopup(self):
		self.__persistDropdown = QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier
		super(MultiComboBox, self).showPopup()

	def hidePopup(self):
		if not self.__persistDropdown:
			super(MultiComboBox, self).hidePopup()

	def __str__(self):
		return ', '.join([str(item) for item in self.checkedItems()])


def main():
	from searchLineEdit import SearchLineEdit
	from  signaltracer import SignalTracer
	tracer = SignalTracer()
	app = QtGui.QApplication(sys.argv)
	app.setStyle(QtGui.QStyleFactory.create("Plastique"))
	import pdb
	#pdb.set_trace()
	lineEdit = SearchLineEdit()
	widget = MultiComboBox()
	tracer.monitor(lineEdit, widget, lineEdit.clearButton)

	widget.setLineEdit(lineEdit)
	lineEdit.clearButtonPressed.connect(widget.clearAll)
	widget.addItems(['item %d' %i for i in xrange(2)])
#	widget.setDefaultText('all')

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

