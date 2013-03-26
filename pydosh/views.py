from PyQt4 import QtCore, QtGui

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
