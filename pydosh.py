import sys
from PyQt4 import QtGui, QtCore
from pydosh.dialogs import LoginDialog
from pydosh.main import PydoshWindow
QtCore.pyqtRemoveInputHook()
import pydosh.pydosh_rc

def main():

	app = QtGui.QApplication(sys.argv)
	app.setWindowIcon(QtGui.QIcon(":/icons/pydosh.png"))

#	if 'linux' in sys.platform:
#		app.setStyle(QtGui.QStyleFactory.create("Plastique"))

	QtCore.QCoreApplication.setApplicationName("pydosh")
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
