from contextlib  import contextmanager
from PyQt4 import QtGui, QtCore

def showWaitCursorDecorator(f):
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

	def blockAllSignals(self):
		try:
			for widget in self.__signalsToBlock:
				widget.blockSignals(True)
			yield
		finally:
			for widget in self.__signalsToBlock:
				widget.blockSignals(False)

@contextmanager
def showWaitCursor():
	""" Context manager utility for showing wait cursor for a code block
	"""
	try:
		QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
		yield
	finally:
		QtGui.QApplication.restoreOverrideCursor()
