from PyQt4 import QtGui, QtCore
QtCore.pyqtRemoveInputHook()
import pdb

from dialogs import unicode_csv_reader

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

				row =  unicode_csv_reader([rawdata.data().decode('utf8')]).next()
				items = [QtGui.QStandardItem(item) for item in row]
#				model.appendRow(items)

if __name__ == "__main__":
	import sys


	# Start the app
	app = QtGui.QApplication(sys.argv)
	model = Model(['test1.csv', 'test2.csv'])
	window = QtGui.QTreeView()
	window.setModel(model)
	window.show()
	app.exec_()
