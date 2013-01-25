from PyQt4 import QtGui, QtCore
from ui_help import Ui_Help
import pydosh_rc


class _HelpBrowser(Ui_Help, QtGui.QDialog):
	def __init__(self, parent=None):
		super(_HelpBrowser, self).__init__(parent=parent)

		self.setAttribute(QtCore.Qt.WA_GroupLeader)
		self.setupUi(self)

		self.closeButton.clicked.connect(self.hide)
		self.treeWidget.itemClicked.connect(self.helpClicked)

		self.treeWidget.header().hide()
		self.splitter.setStretchFactor( 0, 1 )
		self.splitter.setStretchFactor( 1, 2 )

		self.textBrowser.setOpenExternalLinks(True)

		homeHelp= QtGui.QTreeWidgetItem(self.treeWidget)
		homeHelp.setText(0, 'Home')
		homeHelp.setData(0, QtCore.Qt.UserRole, QtCore.QVariant('qrc:/doc/index.html'))

		mainHelp = QtGui.QTreeWidgetItem(homeHelp)
		mainHelp.setText(0, 'Main Window')
		mainHelp.setData(0, QtCore.Qt.UserRole, QtCore.QVariant('qrc:/doc/main.html'))

		loginHelp = QtGui.QTreeWidgetItem(homeHelp)
		loginHelp.setText(0, 'Login')
		loginHelp.setData(0, QtCore.Qt.UserRole, QtCore.QVariant('qrc:/doc/login.html'))

		optionsHelp = QtGui.QTreeWidgetItem(homeHelp)
		optionsHelp.setText(0, 'Options')
		optionsHelp.setData(0, QtCore.Qt.UserRole, QtCore.QVariant('qrc:/doc/options.html'))

		importHelp = QtGui.QTreeWidgetItem(homeHelp)
		importHelp.setText(0, 'Import')
		importHelp.setData(0, QtCore.Qt.UserRole, QtCore.QVariant('qrc:/doc/import.html'))

		self.treeWidget.expandItem(homeHelp)

	def helpClicked(self, item):
		self.showDocumentation(item.data(0, QtCore.Qt.UserRole).toString())

	def showDocumentation(self, path):
		self.setWindowTitle('Help: %s' % self.textBrowser.documentTitle())
		self.textBrowser.setSource(QtCore.QUrl(path))
		self.show()

	def showPage(self, page):
		self.showDocumentation('qrc:/doc/%s' % page)

__helpBroswerInstance = None

def HelpBrowser(parent):
	global __helpBroswerInstance
	if  __helpBroswerInstance is None:
		__helpBroswerInstance = _HelpBrowser(parent)
	return __helpBroswerInstance
