"""
	This widget is a Python port of QxtCheckComboBox from http://dev.libqxt.org/libqxt/src
	(published under public license, but not specifically GPL)
"""
from PySide import QtCore, QtGui
import pydosh_rc
import utils

class MultiComboBoxModel(QtGui.QStandardItemModel):

	checkStateChanged = QtCore.Signal()

	def __init__(self, parent=None):
		super(MultiComboBoxModel, self).__init__(0, 1, parent)

	def flags(self, index):
		return super(MultiComboBoxModel, self).flags(index) | QtCore.Qt.ItemIsUserCheckable

	def data(self, index, role):
		value = super(MultiComboBoxModel, self).data(index, role)

		if index.isValid() and role == QtCore.Qt.CheckStateRole and value is None:
			value = QtCore.Qt.Unchecked

		return value

	def setData(self, index, value, role):
		result = super(MultiComboBoxModel, self).setData(index, value, role)

		if result and role == QtCore.Qt.CheckStateRole:
			self.dataChanged.emit(index, index)
			self.checkStateChanged.emit()
		return result

class MultiComboBox(QtGui.QComboBox):
	""" Extension of QComboBox widget that allows for multiple selection
	"""
	# Signal containing list of selected items
	selectionChanged = QtCore.Signal(list)

	def __init__(self, parent=None):
		super(MultiComboBox, self).__init__(parent=parent)

		self._defaultText = ''
		self.__persistDropdown = False

		self.setLineEdit(QtGui.QLineEdit())
		self.setInsertPolicy(QtGui.QComboBox.NoInsert)
		self.lineEdit().blockSignals(True)
		self.lineEdit().setReadOnly(True)

		self.setModel(MultiComboBoxModel(self))
		self.model().checkStateChanged.connect(self.__updateCheckedItems)
		self.model().rowsInserted.connect(self.__updateCheckedItems)
		self.model().rowsRemoved.connect(self.__updateCheckedItems)

		self.view().installEventFilter(self)
		self.view().window().installEventFilter(self)
		self.view().viewport().installEventFilter(self)
		self.installEventFilter(self)

		self.clearMenu = QtGui.QMenu(self)
		self.clearMenu.addAction(QtGui.QIcon(':/icons/cross.png'), 'Clear All')

		self.activated[int].connect(self.__toggleCheckState)

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
		""" Set all the items as unchecked
		"""

		with utils.signalsBlocked(self.model()):
			for row in xrange(self.model().rowCount()):
				self.setItemData(row, QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

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
		""" Toggles the check state for the supplied item index
		"""
		oldValue = self.itemData(index, QtCore.Qt.CheckStateRole)
		newValue = QtCore.Qt.Checked if (oldValue == QtCore.Qt.Unchecked) else QtCore.Qt.Unchecked
		self.setItemData(index, newValue, QtCore.Qt.CheckStateRole)

	def checkedItems(self):
		""" Returns a list of checked item indexes
		"""
		if self.model():
			currentIndex = self.model().index(0, self.modelColumn(), self.rootModelIndex())
			indexes = self.model().match(currentIndex, QtCore.Qt.CheckStateRole, QtCore.Qt.Checked, -1, QtCore.Qt.MatchExactly)
			return [str(index.data()) for index in indexes]
		return []

	def contextMenuEvent(self, event):
		""" Event for create context menu.

			Args:
				event (QEvent): mouse right click event.
		"""
		if self.clearMenu.exec_(QtGui.QCursor.pos()):
			self.clearAll()

	def __updateCheckedItems(self):
		""" Re-draw the dropdown to reflect check state for all items
			If no items are checked then the default text is shown in the QLineEdit
		"""
		items = self.checkedItems()
		if items:
			self.setEditText(', '.join(items))
		else:
			self.setEditText(self._defaultText)

		self.selectionChanged.emit(items)

	def showPopup(self):
		self.__persistDropdown = QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier
		super(MultiComboBox, self).showPopup()

	def hidePopup(self):
		if not self.__persistDropdown:
			super(MultiComboBox, self).hidePopup()


def main():
#	from  signaltracer import SignalTracer
#	tracer = SignalTracer()
	app = QtGui.QApplication(sys.argv)
	app.setStyle(QtGui.QStyleFactory.create("Plastique"))
	widget = QtGui.QWidget()
	layout = QtGui.QVBoxLayout()
	combo = MultiComboBox()
	layout.addWidget(combo)
	widget.setLayout(layout)

	#tracer.monitor(lineEdit, widget, lineEdit.clearButton)
	combo.addItems(['item %d' %i for i in xrange(5)])
	combo.setDefaultText('all')

	combo.setItemData(2, QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
	combo.setItemData(4, QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)

	widget.show()

	return app.exec_()	


if __name__ == '__main__':
	import sys
	sys.exit(main())
