import sys
import logging
import argparse
from PyQt5 import QtGui, QtCore, Qt, QtWidgets
from .dialogs import LoginDialog
from .mainWindow import PydoshWindow
import pdb
from . import stylesheet
from . import pydosh_rc


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Debug')
    args = parser.parse_args()

    app = Qt.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(":/icons/pydosh.png"))

    QtCore.QCoreApplication.setApplicationName("pydosh")
    QtCore.QCoreApplication.setOrganizationName("innerhippy")
    QtCore.QCoreApplication.setOrganizationDomain("innerhippy.com")
    pdb.set_trace()

    stylesheet.setStylesheet()

    logFormatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)

    logger = logging.getLogger('pydosh')
    logger.addHandler(consoleHandler)
    level = logging.DEBUG if args.debug else logging.ERROR
    logger.setLevel(level)

    loginDialog = LoginDialog()
    loginDialog.show()
    loginDialog.raise_()

    status = -1

    if loginDialog.exec_():
        try:
            window = PydoshWindow()
            window.show()
            status = app.exec_()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                None,
                'Error',
                str(exc),
                QtWidgets.QMessageBox.Ok
            )

    return status

if __name__ == '__main__':
    sys.exit(main())
