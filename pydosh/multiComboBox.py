from PyQt4 import QtCore, QtGui

from models import CheckComboModel

class MultiComboBox(QtGui.QComboBox):
	""" Extension of QComboBox widget that allows for multiple selection
	"""
	checkedItemsChanged = QtCore.pyqtSignal('PyQt_PyObject')
	selectionChanged = QtCore.pyqtSignal()

	def __init__(self, parent=None):
		super(MultiComboBox, self).__init__(parent=parent)

		self._defaultText = ''
		model = CheckComboModel(self)
		self.__selectedItems = None

		self.activated[int].connect(self.__toggleCheckState)

		self.setModel(model)

		lineEdit = QtGui.QLineEdit(self)
		lineEdit.setReadOnly(True)
		self.setLineEdit(lineEdit)
		self.setInsertPolicy(QtGui.QComboBox.NoInsert)

		lineEdit.installEventFilter(self)
		self.view().installEventFilter(self)
		self.view().window().installEventFilter(self)
		self.view().viewport().installEventFilter(self)

		self.__persistDropdown = False

	def setModel(self, model):
		model.checkStateChanged.connect(self.__updateCheckedItems)
		model.rowsInserted.connect(self.__updateCheckedItems)
		model.rowsRemoved.connect(self.__updateCheckedItems)
		super(MultiComboBox, self).setModel(model)

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
			# Persist the dropdown if we haven't clicked outside the combo box and we have a
			# control key held down
			self.__persistDropdown = (receiver != self.view().window())
			print 'mouse press event: in window:%s, persist: %s' % (receiver == self.view().window(), self.__persistDropdown)


		elif event.type() == QtCore.QEvent.MouseButtonRelease:
			# Only keep the dropdown open if we have the shift key pressed
			self.__persistDropdown = QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier
			print 'mouse release event, persist: ', self.__persistDropdown 

		return False

	def __toggleCheckState(self, index):
		value = self.itemData(index, QtCore.Qt.CheckStateRole)
		if self.sender() == self.lineEdit():
			return

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

	def __updateCheckedItems(self, ):
		items = self.checkedItems()

		if len(items) == 0:
			self.setEditText(self._defaultText)
		else:
			self.setEditText(', '.join([str(item) for item in items]))

		self.checkedItemsChanged.emit(items)

	def showPopup(self):
		self.__selectedItems = self.checkedItems()
		super(MultiComboBox, self).showPopup()

	def hidePopup(self):
		print 'keep open?', self.__persistDropdown
		if not self.__persistDropdown:
			if self.checkedItems() != self.__selectedItems:
				self.selectionChanged.emit()
			super(MultiComboBox, self).hidePopup()


def main():
#	from  signaltracer import SignalTracer
	tracer = SignalTracer()
	app = QtGui.QApplication(sys.argv)
	app.setStyle(QtGui.QStyleFactory.create("Plastique"))

	widget = MultiComboBox()
#	tracer.monitor(widget, widget.lineEdit(), widget.model())

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

