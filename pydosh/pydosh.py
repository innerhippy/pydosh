import sys
from PyQt4 import QtGui, QtCore
from main import PyDoshDialog

def main():

	app = QtGui.QApplication(sys.argv)
	window = PyDoshDialog()
	window.show()
	return app.exec_()


if __name__ == '__main__':
	sys.exit(main())
