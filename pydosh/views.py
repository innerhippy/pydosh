from PyQt4 import QtCore, QtGui
import stylesheet

class TagTableView(QtGui.QTableView):
	def __init__(self, parent=None):
		super(TagTableView, self).__init__(parent=parent)

	def sizeHint(self):
		width = 0
		for column in xrange(self.model().columnCount()):
			width += self.columnWidth(column)

		width += self.verticalHeader().width() + self.autoScrollMargin() * 1.5 + 2

		height=0
		for row in xrange(self.model().rowCount()):
			height += self.rowHeight(row)

		height += self.horizontalHeader().height() + self.autoScrollMargin() * 1.5 + 2
		return QtCore.QSize(width, height)
	
class RecordTableView(QtGui.QTableView):
	def __init__(self, parent=None):
		super(RecordTableView, self).__init__(parent=parent)
		self._creditColour = QtGui.QColor()
		self._debitColour = QtGui.QColor()
		stylesheet.setStylesheet()

	@QtCore.pyqtProperty(QtGui.QColor)
	def creditColour(self):
		return self._creditColour

	@creditColour.setter
	def creditColour(self, value):
		self._creditColour = value

	@QtCore.pyqtProperty(QtGui.QColor)
	def debitColour(self):
		return self._debitColour

	@debitColour.setter
	def debitColour(self, value):
		self._debitColour = value
