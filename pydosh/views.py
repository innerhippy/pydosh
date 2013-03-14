from PyQt4 import QtCore, QtGui

class TagTableView(QtGui.QTableView):
	def __init__(self, parent=None):
		super(TagTableView, self).__init__(parent=parent)

	def sizeHint(self):
		width = 0
		for column in xrange(self.model().columnCount()):
			width += self.columnWidth(column)

		return QtCore.QSize(2+width, 20+self.height())
