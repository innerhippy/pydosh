import sys
from PyQt4 import QtGui, QtCore
from main import PydoshWindow

def main():

	app = QtGui.QApplication(sys.argv)
	window = PydoshWindow()
	window.show()
	return app.exec_()


if __name__ == '__main__':
	sys.exit(main())
