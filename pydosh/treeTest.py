from PyQt4 import QtGui, QtCore
QtCore.pyqtRemoveInputHook()
import pdb
import sys

from dialogs import unicode_csv_reader

def main():
	app = QtGui.QApplication(sys.argv)
#	root = QtCore.QObject()
#	root.setObjectName("root")
#
#	foo = QtCore.QObject(root) 
#	foo.setObjectName( "foo" )
#	child = QtCore.QObject( foo )
#	child.setObjectName( "Mark" )
#	child = QtCore.QObject( foo )
#	child.setObjectName( "Bob" )
#	child = QtCore.QObject( foo )
#	child.setObjectName( "Kent" )
#	
#	bar = QtCore.QObject(root)
#	bar.setObjectName( "bar" )
#
#	child = QtCore.QObject( bar )
#	child.setObjectName( "Ole" )
#	child = QtCore.QObject( bar )
#	child.setObjectName( "Trond" )
#	child = QtCore.QObject( bar )
#	child.setObjectName( "Kjetil" )
#	child = QtCore.QObject( bar );
#	child.setObjectName( "Lasse" )
#
#	baz = QtCore.QObject(root)
#	baz.setObjectName( "baz" )
#	child = QtCore.QObject( baz )
#	child.setObjectName( "Bengt" )
#	child = QtCore.QObject( baz )
#	child.setObjectName( "Sven" )

	root = TreeItem()
	row1 = root.addChild(TreeItem(['aaa'], root))
	row2 = root.addChild(TreeItem(['bbb', 'ccc'], root))
	
	model = ObjectTreeModel(root)

	tree = QtGui.QTreeView()
	tree.setModel(model)

	tree.show()

	return app.exec_()

class TreeItem(object):
	def __init__(self, data=[], parent=None):
		super(TreeItem, self).__init__()
		self._data = data
		self._parent = parent
		self._children = []

	def addChild(self, child):
		self._children.append(child)

	def child(self, row):
		return self._children[row]

	def childCount(self):
		return len(self._children)
	
	def columnCount(self):
		return len(self._data)

	def data(self, column):
		return self._data[column]

	def parent(self):
		return self._parent

	def row(self):
		if self._parent is not None:
			return self._parent.index(self)
		return 0

class ObjectTreeModel(QtCore.QAbstractItemModel):
	def __init__(self, root, parent=None):
		super(ObjectTreeModel, self).__init__(parent=parent)
		self.root = root

	def flags(self, index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

	def data(self, index, role=QtCore.Qt.DisplayRole):

		if not index.isValid():
			return QtCore.QVariant()

		if role == QtCore.Qt.DisplayRole:
			if index.column() == 0:
				return index.internalPointer().objectName()
			elif index.column() == 1:
				return index.internalPointer().metaObject().className()
	
		elif role == QtCore.Qt.ToolTipRole:
			if index.column() == 0:
				return 'The name of the object.'
			if index.column() == 1:
				return 'The name of the class.'

		return QtCore.QVariant()

	def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
		if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
			return QtCore.QVariant()
		if section == 0:
			return QtCore.QString( "Object" )
		elif section == 1:
			return QtCore.QString( "Class" )
		return QtCore.QVariant()

	def rowCount(self, parent=QtCore.QModelIndex()):

		if parent.column() > 0:
			return 0

		if not parent.isValid():
			parent = self.root
		else:
			parent = parent.internalPointer()

		return parent.childCount()

	def columnCount(self, parent=QtCore.QModelIndex()):
		if parent.isValid():
			return parent.internalPointer().columnCount()
		return self.root.columnCount()

	def index(self, row, column, parent=QtCore.QModelIndex() ):

		if not self.hasIndex(row, column, parent):
			return QtCore.QModelIndex()

		if not parent.isValid():
			parentObject = self.root
		else:
			parentObject = parent.internalPointer()

		childItem = parentObject.child(row)

		if childItem:
			return self.createIndex( row, column, childItem )
		else:
			return QtCore.QModelIndex()

	def parent(self, index):

		if not index.isValid():
			return QtCore.QModelIndex()

		child = index.internalPointer()
		parent = child.parent()

		if parent == self.root:
			return QtCore.QModelIndex()

		return self.createIndex(parent.row(), 0, parent)


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
