from PyQt4 import QtGui, QtCore

def showWaitCursor(f):
	""" Decorator for display a wait cursor whilst in a slow function
	"""
	def new_f(*args, **kwargs):
		QtGui.QApplication.setOverrideCursor( QtCore.Qt.WaitCursor )
		try:
			return f(*args, **kwargs)
		finally:
			QtGui.QApplication.restoreOverrideCursor()
	new_f.__name__ = f.__name__
	new_f.__doc__  = f.__doc__
	return new_f

