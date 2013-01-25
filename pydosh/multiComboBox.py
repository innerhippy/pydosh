from PyQt4 import QtCore, QtGui
from models import CheckComboModel

class MultiComboBox(QtGui.QComboBox):
	""" Extension of QComboBox widget that allows for multiple selection
	"""
	checkedItemsChanged = QtCore.pyqtSignal('PyQt_PyObject')

	def __init__(self, parent=None):
		super(MultiComboBox, self).__init__(parent=parent)
		
		model = CheckComboModel(self)
		
		self.activated.connect(self.__toggleCheckState)
		model.checkStateChanged.connect(self.__toggleCheckState)
		model.checkStateChanged.connect(self.__updateCheckedItems)
		model.rowsInserted.connect(self.__updateCheckedItems)
		model.rowsRemoved.connect(self.__updateCheckedItems)
		
		self.setModel(model)

		lineEdit = QtGui.QLineEdit(self)
		lineEdit.setReadOnly(True)
		self.setLineEdit(lineEdit)
		#lineEdit.disconnect(self, QtCore.SIGNAL('textChanged(QString)'))
		self.setInsertPolicy(QtGui.QComboBox.NoInsert)
		
		self.view().installEventFilter(self)
		self.view().window().installEventFilter(self)
		self.view().viewport().installEventFilter(self)

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

		if len(items) == 0:
			self.setEditText('')
		else:
			self.setEditText(', '.join([str(item) for item in items]))

		self.checkedItemsChanged.emit(items)

	def hidePopup(self):
		if self.__containerMousePress:
			super(MultiComboBox, self).hidePopup()
