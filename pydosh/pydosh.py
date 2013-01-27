import sys
import pdb
from PyQt4 import QtGui, QtCore
from main import PydoshWindow
from dialogs import LoginDialog
QtCore.pyqtRemoveInputHook()

def main():

	app = QtGui.QApplication(sys.argv)
	app.setStyle(QtGui.QStyleFactory.create("Plastique"))

	QtCore.QCoreApplication.setApplicationName("doshlogger")
	QtCore.QCoreApplication.setOrganizationName("innerhippy")
	QtCore.QCoreApplication.setOrganizationDomain("innerhippy.com")

	loginDialog = LoginDialog()

	if loginDialog.exec_():
		window = PydoshWindow()
		window.show()
		return app.exec_()

	return -1

if __name__ == '__main__':
	sys.exit(main())
