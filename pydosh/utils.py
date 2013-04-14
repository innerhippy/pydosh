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

class _BlockSignals(object):
	_refs = {}
	def __init__(self):
		super(_BlockSignals, self).__init__()

	@contextmanager
	def __call__(self, widget):
		self._refs.setdefault(widget, 0)
		self._refs[widget] += 1

		try:
			widget.blockSignals(True)
			yield
		finally:
			if self._refs[widget] == 1:
				self._refs.pop(widget)
				widget.blockSignals(False)
			else:
				# don't unblock - another call to block is in progress
				self._refs[widget] -= 1

blockSignals = _BlockSignals()

@contextmanager
def showWaitCursor():
	""" Context manager utility for showing wait cursor for a code block
	"""
	try:
		QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
		yield
	finally:
		QtGui.QApplication.restoreOverrideCursor()
