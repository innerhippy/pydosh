from PyQt4 import QtCore, QtGui
import utils
import pydosh_rc

class MultiComboBox(QtGui.QComboBox):
	""" Extension of QComboBox widget that allows for multiple selection
	"""
	# Signal containing list of selected indexes
	selectionChanged = QtCore.pyqtSignal('PyQt_PyObject')

	def __init__(self, parent=None):
		super(MultiComboBox, self).__init__(parent=parent)

		self._defaultText = ''
		self.__persistDropdown = False

		self.setLineEdit(QtGui.QLineEdit())
		self.setInsertPolicy(QtGui.QComboBox.NoInsert)
		self.lineEdit().blockSignals(True)

		self.view().installEventFilter(self)
		self.view().window().installEventFilter(self)
		self.view().viewport().installEventFilter(self)
		self.installEventFilter(self)

		self.activated[int].connect(self.__toggleCheckState)

	def reset(self):
		""" Reset the model and clear selection if necessary
		"""
		itemsBefore = [index.data().toString() for index in self.__checkedItems()]

		self.model().select()

		itemsAfter = [index.data().toString() for index in self.__checkedItems()]

		if itemsBefore != itemsAfter:
			self.clearAll()

	def setModel(self, model):
		super(MultiComboBox, self).setModel(model)
		# This is a bit odd, but seem to need it
		self.setModelColumn(self.modelColumn())
		model.rowsInserted.connect(self.__updateCheckedItems)
		model.rowsRemoved.connect(self.__updateCheckedItems)
		model.dataChanged.connect(self.__updateCheckedItems)
		self.__updateCheckedItems()

	def dataChanged(self):
		""" Indicates if the underlying data has been updated. 
		"""
		self.model().select()

	def __checkAll(self, check=False):
		""" Function to set all the items as checked or unchecked based on the argument.

			Args:
				check(bool): check state
		"""
		searchState = QtCore.Qt.Unchecked if check else QtCore.Qt.Checked
		assignState = QtCore.Qt.Checked if check else QtCore.Qt.Unchecked

		modelIndex = self.model().index(0, self.modelColumn(), self.rootModelIndex())
		modelIndexList = self.model().match(modelIndex, QtCore.Qt.CheckStateRole, searchState, -1, QtCore.Qt.MatchExactly)

		with utils.signalsBlocked(self.model()):
			for index in modelIndexList:
				self.setItemData(index.row(), assignState, QtCore.Qt.CheckStateRole)

		self.__updateCheckedItems()

	def setLineEdit(self, edit):
		edit.setReadOnly(True)
		edit.installEventFilter(self)
		super(MultiComboBox, self).setLineEdit(edit)

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

	def clearAll(self):
		""" Event for clear all check from the list view. 
		"""
		self.__checkAll(False)

	def checkAll(self):
		""" Event for check all from the list view.
		"""
		self.__checkAll(True)

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
		value = self.itemData(index, QtCore.Qt.CheckStateRole)

		if value.isValid():
			if value.toPyObject() == QtCore.Qt.Unchecked:
				state = QtCore.Qt.Checked
			else:
				state = QtCore.Qt.Unchecked
			self.setItemData(index, state, QtCore.Qt.CheckStateRole)

	def __checkedItems(self):
		indexes = []
		if self.model():
			currentIndex = self.model().index(0, self.modelColumn(), self.rootModelIndex())
			indexes = self.model().match(currentIndex, QtCore.Qt.CheckStateRole, QtCore.Qt.Checked, -1, QtCore.Qt.MatchExactly)
		return indexes

	def contextMenuEvent(self, event):
		""" Event for create context menu.
			Args:
				event (QEvent): mouse right click event.
		"""
		quitAction = QtGui.QAction('&Quit', self)
		quitAction.setShortcut('Alt+q')
		quitAction.setStatusTip('Exit the program')
		quitAction.setIcon(QtGui.QIcon(':/icons/exit.png'))

		signalMap = {}
		contextMenu = QtGui.QMenu()

		clearAllAction = contextMenu.addAction(QtGui.QIcon(':/icons/cross.png'), 'Clear All')
		clearAllAction.setIconVisibleInMenu(True)
		signalMap[clearAllAction] = self.clearAll
		checkAllAction = contextMenu.addAction(QtGui.QIcon(':/icons/tick.png'), 'Check All')
		checkAllAction.setIconVisibleInMenu(True)
		signalMap[checkAllAction] = self.checkAll

		contextMenuAction = contextMenu.exec_(QtGui.QCursor.pos())
		if contextMenuAction and signalMap.has_key(contextMenuAction):
			signalMap[contextMenuAction]()

	def __updateCheckedItems(self):
		items = self.__checkedItems()
		if items:
			self.setEditText(QtCore.QStringList([index.data().toString() for index in items]).join(', '))
		else:
			self.setEditText(self._defaultText)

		self.selectionChanged.emit(items)

	def showPopup(self):
		self.__persistDropdown = QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier
		super(MultiComboBox, self).showPopup()

	def hidePopup(self):
		if not self.__persistDropdown:
			super(MultiComboBox, self).hidePopup()


class MyCombo(QtGui.QComboBox):
	def __init__(self, parent=None):
		super(MyCombo, self).__init__(parent=parent)

	def paintEvent(self, event):
		painter = QtGui.QStylePainter(self)
		opt = QtGui.QStyleOptionComboBox()
		self.initStyleOption(opt)
		#painter.drawComplexControl(QtGui.QStyle.CC_ComboBox, opt)
		#painter.drawControl(QtGui.QStyle.CE_ComboBoxLabel, opt)
#		super(MyCombo, self).paintEvent(event)



def main():
	from searchlineedit import SearchLineEdit
#	from  signaltracer import SignalTracer
#	tracer = SignalTracer()
	app = QtGui.QApplication(sys.argv)
	#app.setStyle(QtGui.QStyleFactory.create("Plastique"))
	#pdb.set_trace()
	#lineEdit = SearchLineEdit()
	combo = MyCombo()
	combo.setFrame(False)
#	combo.setStyleSheet ("QComboBox::drop-down {border-width: 0px;} QComboBox::down-arrow {image: url(noimg); border-width: 0px;}")
	#tracer.monitor(lineEdit, widget, lineEdit.clearButton)

	#widget.setLineEdit(lineEdit)
	#lineEdit.clearButtonPressed.connect(widget.clearAll)
	label = QtGui.QLabel('releaseTime')
	combo.addItem(QtGui.QIcon('in.png'), '')
	combo.addItem(QtGui.QIcon('ca.png'), '')
	combo.addItem(QtGui.QIcon('gb.png'), '')
	combo.addItem(QtGui.QIcon('us.png'), '')
	#widget.addItems(['item %d' %i for i in xrange(2)])
#	widget.setDefaultText('all')

	dialog = QtGui.QDialog()
	layout = QtGui.QVBoxLayout()
	hLayout = QtGui.QHBoxLayout()
	hLayout.addWidget(label)
	hLayout.addWidget(combo)
	layout.addLayout(hLayout)

	dialog.setLayout(layout)
	dialog.show()

	app.exec_()	
	return 0



if __name__ == '__main__':
	import sys
	sys.exit(main())

