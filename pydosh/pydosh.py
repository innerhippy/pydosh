import sys
from PyQt4 import QtGui, QtCore
from main import PydoshWindow
from dialogs import LoginDialog
QtCore.pyqtRemoveInputHook()

def main():

	app = QtGui.QApplication(sys.argv)

	QtCore.QCoreApplication.setApplicationName("doshlogger")
	QtCore.QCoreApplication.setOrganizationName("innerhippy")
	QtCore.QCoreApplication.setOrganizationDomain("innerhippy.com")

	loginDialog = LoginDialog()
	# TODO: remove!
	#if True or loginDialog.exec_():
	if loginDialog.exec_():
		window = PydoshWindow()
		window.show()
		return app.exec_()

	return -1

if __name__ == '__main__':
	sys.exit(main())
