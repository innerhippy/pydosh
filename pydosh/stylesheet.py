from PySide import QtGui, QtCore

__styleNames = ['Default', 'Dark']

def styleSheetNames():
	return __styleNames

def setStylesheet(name=None):
	""" Set the stylesheet from the resource settings.
		If no stylesheet name is supplied then the value from the
		config is read
	"""
	settings = QtCore.QSettings()

	if name is None:
		name = settings.value("options/stylesheet", __styleNames[0])

	if name not in __styleNames:
		QtGui.QMessageBox.warning(
			None, 
			'Stylesheet Error',
			'Stylesheet %r not recognised - must be one of %r' % (
				name, ', '.join(__styleNames)),
			QtGui.QMessageBox.Ok
		)
		name = __styleNames[0]

	styleSheetFile = QtCore.QFile(':/style/%s' % name)
	styleSheetFile.open(QtCore.QIODevice.ReadOnly)
	styleSheet = styleSheetFile.readAll()

	QtGui.QApplication.instance().setStyleSheet(str(styleSheet))
	settings.setValue('options/stylesheet', name)
