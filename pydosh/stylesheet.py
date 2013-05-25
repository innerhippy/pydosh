from PyQt4 import QtGui, QtCore

__styleNames = ['Default', 'Dark']

def styleSheetNames():
	return __styleNames

def setStylesheet(name=None):
	settings = QtCore.QSettings()

	if name is None:
		name = settings.value("options/stylesheet", 'Default').toString()

	styleSheetFile = QtCore.QFile(':/style/%s' % name)
	styleSheetFile.open(QtCore.QIODevice.ReadOnly)
	styleSheet = QtCore.QString(styleSheetFile.readAll())

	QtGui.QApplication.instance().setStyleSheet(styleSheet)
	settings.setValue('options/stylesheet', name)
