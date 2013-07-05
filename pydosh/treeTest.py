from PyQt4 import QtGui, QtCore
QtCore.pyqtRemoveInputHook()
import pdb
import sys

from dialogs import unicode_csv_reader

class TreeItem(object):
	def __init__(self):
		super(TreeItem, self).__init__()
		self._parent = None
		self._children = []

	def setParent(self, parent):
		self._parent = parent

	def appendChild(self, child):
		child.setParent(self)
		self._children.append(child)

	def child(self, row):
		return self._children[row]

	def childCount(self):
		return len(self._children)

	def columnCount(self):
		raise NotImplementedError

	def data(self, column):
		raise NotImplementedError

	def parent(self):
		return self._parent

	def indexOf(self, child):
		return self._children.index(child)

	def row(self):
		if self._parent:
			return self._parent.indexOf(self)
		return 0

class CsvFileItem(TreeItem):
	def __init__(self, filename):
		super(CsvFileItem, self).__init__()
		self._filename = filename

	def columnCount(self):
		return 1

	def data(self, column):
		if column == 0:
			return self._filename
		return QtCore.QVariant()

class CsvRecordItem(TreeItem):
	def __init__(self, rawData):
		super(CsvRecordItem, self).__init__()
		self._rawData = rawData
		self._fields = unicode_csv_reader([rawData.data().decode('utf8')]).next()

	def columnCount(self):
		return len(self._fields)

	def data(self, column):
		try:
			return self._fields[column]
		except IndexError:
			return QtCore.QVariant()

class TreeModel(QtCore.QAbstractItemModel):
	def __init__(self, files, parent=None):
		super(TreeModel, self).__init__(parent=parent)
		self._numColumns = 0
		self._root = TreeItem()
		for item in self.readFiles(files):
			self._root.appendChild(item)

	def getNodeItem(self, index):
		if index.isValid():
			return index.internalPointer()
		return self._root

	def readFiles(self, files):
		for filename in files:
			item = CsvFileItem(filename)
			csvfile = QtCore.QFile(filename)

			if not csvfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
				raise Exception('Cannot open file %r' % filename)

			while not csvfile.atEnd():
				rawData = csvfile.readLine().trimmed()
				recItem = CsvRecordItem(rawData)
				self._numColumns = max(self._numColumns, recItem.columnCount())
				item.appendChild(recItem)
			yield item

	def columnCount(self, parent=QtCore.QModelIndex()):
		return self._numColumns

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid():
			return QtCore.QVariant()

		if role != QtCore.Qt.DisplayRole:
			return QtCore.QVariant()

		item = self.getNodeItem(index)
		return item.data(index.column())

	def flags(self, index):
		if not index.isValid():
			return 0

		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

	def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
		return QtCore.QVariant()

	def index(self, row, column, parent=QtCore.QModelIndex()):

		if not self.hasIndex(row, column, parent):
			return QtCore.QModelIndex()

		parentItem = self.getNodeItem(parent)
		childItem = parentItem.child(row)

		if childItem:
			return self.createIndex( row, column, childItem)

		return QtCore.QModelIndex()

	def parent(self, index):

		if not index.isValid():
			return QtCore.QModelIndex()

		childItem = self.getNodeItem(index)
		parentItem = childItem.parent()

		if parentItem == self._root:
			return QtCore.QModelIndex()

		return self.createIndex(parentItem.row(), 0, parentItem)

	def rowCount(self, parent=QtCore.QModelIndex()):

		if parent.column() > 0:
			return 0

		item = self.getNodeItem(parent)
		return item.childCount()

def main():
	app = QtGui.QApplication(sys.argv)
	model = TreeModel(['test1.csv', 'test2.csv'])

	tree = QtGui.QTreeView()
	tree.setModel(model)

	tree.show()

	return app.exec_()

if __name__ == "__main__":
	import sys
	sys.exit(main())
