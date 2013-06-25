from PyQt4 import QtGui, QtCore
QtCore.pyqtRemoveInputHook()
import pdb
import sys

from dialogs import unicode_csv_reader

def main():
	app = QtGui.QApplication(sys.argv)
	root = QtCore.QObject()
	root.setObjectName("root")

	foo = QtCore.QObject(root) 
	foo.setObjectName( "foo" )
	child = QtCore.QObject( foo )
	child.setObjectName( "Mark" )
	child = QtCore.QObject( foo )
	child.setObjectName( "Bob" )
	child = QtCore.QObject( foo )
	child.setObjectName( "Kent" )
	
	bar = QtCore.QObject(root)
	bar.setObjectName( "bar" )

	child = QtCore.QObject( bar )
	child.setObjectName( "Ole" )
	child = QtCore.QObject( bar )
	child.setObjectName( "Trond" )
	child = QtCore.QObject( bar )
	child.setObjectName( "Kjetil" )
	child = QtCore.QObject( bar );
	child.setObjectName( "Lasse" )

	baz = QtCore.QObject(root)
	baz.setObjectName( "baz" )
	child = QtCore.QObject( baz )
	child.setObjectName( "Bengt" )
	child = QtCore.QObject( baz )
	child.setObjectName( "Sven" )

	model = ObjectTreeModel(root)

	tree = QtGui.QTreeView()
	tree.setModel(model)

	tree.show()

	return app.exec_()

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

		if not parent.isValid():
			parentObject = self.root
		else:
			parentObject = parent.internalPointer()

		return len(parentObject.children())

	def columnCount(self, parent=QtCore.QModelIndex()):
		return 2

	def index(self, row, column, parent=QtCore.QModelIndex() ):

		if not parent.isValid():
			parentObject = self.root
		else:
			parentObject = parent.internalPointer()

		if row < len(parentObject.children()):
			return self.createIndex( row, column, parentObject.children()[row] )
		else:
			return QtCore.QModelIndex()

	def parent(self, index):

		if not index.isValid():
			return QtCore.QModelIndex()

		indexObject = index.internalPointer()
		parentObject = indexObject.parent()

		if parentObject == self.root:
			return QtCore.QModelIndex()

		grandParentObject = parentObject.parent()

		return self.createIndex( grandParentObject.children().index( parentObject ), 0, parentObject )


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
