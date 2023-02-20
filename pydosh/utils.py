try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

from contextlib  import contextmanager
from PyQt5 import QtCore, Qt

def flattenArgs(items):
    """ Generator to expand a sequence of items recursively.
        Eg (1, [2, 3], ["a", "b", [10]]) -> (1, 2, 3, "a", "b", 10)
    """
    for item in items:
        if isinstance(item, Iterable) and not isinstance(item, str):
            for sub in flattenArgs(item):
                yield sub
        else:
            yield item

@contextmanager
def signalsBlocked(*args):
    """ Block signals with context manager
        Args: 
            args: widget or widgets
    """
    states = [(target, target.signalsBlocked()) for target in flattenArgs(args) if target is not None]
    try:
        for target, _ in states:
            target.blockSignals(True)
        yield
    finally:
        for target, blockedState in states:
            target.blockSignals(blockedState)

def showWaitCursorDecorator(f):
    """ Decorator for display a wait cursor whilst in a slow function
    """
    def new_f(*args, **kwargs):
        Qt.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            return f(*args, **kwargs)
        finally:
            Qt.QApplication.restoreOverrideCursor()
    new_f.__name__ = f.__name__
    new_f.__doc__  = f.__doc__
    return new_f

@contextmanager
def showWaitCursor():
    """ Context manager utility for showing wait cursor for a code block
    """
    try:
        Qt.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        yield
    finally:
        Qt.QApplication.restoreOverrideCursor()
