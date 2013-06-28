from PyQt4 import QtGui, QtCore
QtCore.pyqtRemoveInputHook()
import pdb
import sys

from dialogs import unicode_csv_reader

def main():
	app = QtGui.QApplication(sys.argv)
	root = TreeItem()#['one', 'two'])
	root.appendChild(TreeItem(['aaa']))
	row1 = TreeItem(['bbb', 'ccc'])
	root.appendChild(row1)
	row1.appendChild(TreeItem(['xxx']))
	row1.appendChild(TreeItem(['yyy', 'zzz']))
	
	model = TreeModel(root)

	tree = QtGui.QTreeView()
	tree.setModel(model)

	tree.show()

	return app.exec_()

class TreeItem(object):
	def __init__(self, data=[]):
		super(TreeItem, self).__init__()
		self._data = data
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
		if self._parent is None:
			return self._children[0].columnCount()
		return len(self._data)

	def data(self, column):
		if column >= len(self._data):
			return QtCore.QVariant()
		return self._data[column]

	def parent(self):
		return self._parent

	def indexOf(self, child):
		return self._children.index(child)

	def row(self):
		if self._parent:
			return self._parent.indexOf(self)
		return 0

	def __str__(self):
		return '%s (%d)' % (', '.join(self._data), id(self))

class TreeModel(QtCore.QAbstractItemModel):
	def __init__(self, root, parent=None):
		super(TreeModel, self).__init__(parent=parent)
		self._root = root

	def columnCount(self, parent=QtCore.QModelIndex()):
		if parent.isValid():
			return parent.internalPointer().columnCount()
		return self._root.columnCount()

	def data(self, index, role=QtCore.Qt.DisplayRole):

		if not index.isValid():
			return QtCore.QVariant()

		if role != QtCore.Qt.DisplayRole:
			return QtCore.QVariant()
		
		item = index.internalPointer()
		return item.data(index.column())

	def flags(self, index):
		if not index.isValid():
			return 0

		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

	def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return self._root.data(section)

		return QtCore.QVariant()

	def index(self, row, column, parent=QtCore.QModelIndex() ):

		if not self.hasIndex(row, column, parent):
			return QtCore.QModelIndex()

		if not parent.isValid():
			parentItem = self._root
		else:
			parentItem = parent.internalPointer()

		childItem = parentItem.child(row)

		if childItem:
			return self.createIndex( row, column, childItem)

		return QtCore.QModelIndex()

	def parent(self, index):

		if not index.isValid():
			return QtCore.QModelIndex()

		childItem = index.internalPointer()
		parentItem = childItem.parent()

		if parentItem == self._root:
			return QtCore.QModelIndex()

		return self.createIndex(parentItem.row(), 0, parentItem)

	def rowCount(self, parent=QtCore.QModelIndex()):

		if parent.column() > 0:
			return 0

		if not parent.isValid():
			parentItem = self._root
		else:
			parentItem = parent.internalPointer()

		return parentItem.childCount()

class Model(QtCore.QAbstractItemModel):
	def __init__(self, csvFiles, parent=None):
		super(Model, self).__init__(parent=parent)

#		pdb.set_trace()
		for filename in csvFiles:
			csvfile = QtCore.QFile(filename)

			if not csvfile.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
				raise Exception('Cannot open file %r' % filename)

			while not csvfile.atEnd():
				rawdata = csvfile.readLine().trimmed()
#				dataDict = self.__rawData.setdefault(filename, [])
#				dataDict.append(rawdata)
				print filename, rawdata

				row = unicode_csv_reader([rawdata.data().decode('utf8')]).next()
				items = [QtGui.QStandardItem(item) for item in row]
#				model.appendRow(items)

if __name__ == "__main__":
	import sys
	main()

#	# Start the app
#	app = QtGui.QApplication(sys.argv)
#	model = Model(['test1.csv', 'test2.csv'])
#	window = QtGui.QTreeView()
#	window.setModel(model)
#	window.show()
#	app.exec_()
