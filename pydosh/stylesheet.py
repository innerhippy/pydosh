from PyQt4 import QtGui, QtCore

__styleSheetMap = {
	'default': None,
	'dark': ':/darkstyle.qss',
}

def styleSheetNames():
	return __styleSheetMap.keys()

def setStylesheet(name=None):
	settings = QtCore.QSettings()

	if name is None:
		name = settings.value("options/stylesheet", 'default').toString()

	styleSheet = QtCore.QString()
	stylesheetResource = __styleSheetMap.get(str(name))
	if stylesheetResource:
		styleSheetFile = QtCore.QFile(stylesheetResource)
		styleSheetFile.open(QtCore.QIODevice.ReadOnly)
		styleSheet = QtCore.QString(styleSheetFile.readAll())

	QtGui.QApplication.instance().setStyleSheet(styleSheet)
	settings.setValue('options/stylesheet', name)
