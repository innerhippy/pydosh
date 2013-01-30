""" General PyQt Utilities
"""
import collections
from contextlib  import contextmanager
from PyQt4 import QtCore, QtGui

@contextmanager
def signalsBlocked(*args):
	""" Block signals with context manager
		Args: 
			args: widget or widgets
	"""
	states = [(target, target.signalsBlocked()) for target in flattenArgs(args)]
	try:
		for target, _ in states:
			target.blockSignals(True)
		yield
	finally:
		for target, blockedState in states:
			target.blockSignals(blockedState)


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

def flattenArgs(items):
	""" Generator to expand a sequence of items recursively.
		Eg (1, [2, 3], ["a", "b", [10]]) -> (1, 2, 3, "a", "b", 10)
	"""
	for item in items:
		if isinstance(item, collections.Iterable) and not isinstance(item, basestring):
			for sub in flattenArgs(item):
				yield sub
		else:
			yield item


class _SignalTracker(QtCore.QObject):
	""" Base class for signal tracking and monitoring. Should not be instantiated directly
	"""
	def __init__(self, showTracer):
		super(_SignalTracker, self).__init__()
		self._showTracer = showTracer
		self._counter = 0

	def monitor(self, *widgets):
		""" Monitor the signals being emitted by one or more objects.
			Accepts single or multiple widgets, or sequences of widgets
		"""
		for widget in flattenArgs(widgets):
			for signal in self._findSignals(widget):
				# Don't want to catch this signal as
				# the widget is just about to die
				if signal.startswith('destroyed'):
					continue

				self.connect(
					widget, QtCore.SIGNAL(signal),
					_SignalTracker.Receiver(widget=widget, sigName=signal, callable=self._recordSignal)
				)

	def _termcode(self, num):
		return '\033[%sm'%num
	#
	# Internal Helpers
	#
	class Receiver(object):
		""" An internal helper class to handle the receiving and aggregation of all
			signals emitted from a number of widgets.

			[For an aggregator across widgets only the QSignalMapper is preferred]
		"""
		def __init__(self, widget, sigName, callable):
			super(_SignalTracker.Receiver, self).__init__()
			self._widget = widget
			self._sigName = sigName
			self._callable = callable

		def __call__(self, *args, **kwargs):
			(self._callable)(self._widget, self._sigName, args, kwargs)

	@staticmethod
	def _findSignals(widget):
		""" Find all signals defined for a given widget

			Returns a generator of signal signatures
		"""
		for idx in xrange(widget.metaObject().methodCount()):
			qtMethod = widget.metaObject().method(idx)
			if qtMethod.methodType() == QtCore.QMetaMethod.Signal:
				yield qtMethod.signature()

	def _recordSignal(self, widget, signal, args, kwargs):
		raise NotImplementedError

	def _printSignal(self, widget, signal, args, kwargs):
		self._counter += 1
		print 'Signal [%04d]: %s[%s] %s %r' % (
				self._counter,
				widget.__class__.__name__,
				widget.objectName(),
				self._termcode(91) + signal + self._termcode(0),
				args)

class SignalTracer(_SignalTracker):
	"""  A logger for Qt Signals for debugging custom widgets.

		**Example**::

			from mpc.pyqtUtils import SignalTracer
			tracer = SignalTracer()

		Create widgets and call monitor::

			comboWidget = ComboWidget()
			textEditWidget = QTextEdit()
			tracer.monitor(comboWidget, textEditWidget)

		Do something to the widgets to trigger signals::

			textEditWidget.setText('some text')
			comboWidget.setCurrentIndex(0)

		Signal details will be output as they are emitted::

			Received: QTextEdit[] textChanged(QString) ('some text',)
			Received: ComboWidget[] currentIndexChanged(QString) ('item 1',)
			Received: ComboWidget[] currentIndexChanged(int) (0,)

	"""

	def __init__(self):
		super(SignalTracer, self).__init__(showTracer=True)

	def _recordSignal(self, widget, signal, args, kwargs):
		self._printSignal( widget, signal, args, kwargs)


class SignalRecorder(_SignalTracker):
	""" A recorder for Qt Signals for debugging and for testing custom widgets.

		**Features**

			*	Handles both builtin and custom signals defined in Python
				so long as a pyqtSignal property exists.
			*	Handles overloading of signals, including builtins.
			*	Optional signalTracer (showTracer=True)

		**Example**::

			from mpc.pyqtUtils import SignalRecorder
			recorder = SignalRecorder()

		Create widgets and call monitor::

			comboWidget = ComboWidget()
			textEditWidget = QTextEdit()
			recorder.monitor(comboWidget, textEditWidget)

		Do something to the widgets to trigger signals::

			textEditWidget.setText('some text')
			comboWidget.setCurrentIndex(0)

		Verify that the signals have been emitted in correctly (in order)::

			recorder.expected('textChanged()', 'some text', widget=textEditWidget)
			recorder.expected('currentIndexChanged(QString)', 'item 1', widget=comboWidget)
			recorder.expected('currentIndexChanged(int)', 0, widget=comboWidget)

		Finally, check that no other signals were emitted::

			assert(recorder.isEmpty())
	"""

	def __init__(self, showTracer=False):
		super(SignalRecorder, self).__init__(showTracer=showTracer)
		self.__stoneTablet = None
		self.reset()

	def __len__(self):
		""" returns the number of items in the queue
		"""
		if self.__stoneTablet is not None:
			return len(self.__stoneTablet)
		return 0

	def reset(self):
		""" Clears the signal queue
		"""
		self.__stoneTablet = collections.deque()

	def playback(self):
		for item in self.__stoneTablet:
			self._printSignal(*item)

	def isEmpty(self):
		""" Returns True if the queue is empty
		"""
		return len(self.__stoneTablet or []) == 0

	def expected(self, signal, *args, **kwargs):
		""" Inspects the next recorded signal in the queue against supplied arguments
			Raises AssertionError if signal details do not match

			Args:
				signal (str) - signature of PyQt signal, eg 'currentIndexChanged(QString)'
				args         - sequence of expected values from the signal
				kwargs       - kwargs of expected signal. supply "widget=myWidget" to differentiate multiple widgets
		"""
		if self.isEmpty():
			raise AssertionError("No signals in the queue, expected %r" % signal)

		widget = kwargs.pop('widget', None)
		gotWidget, gotSignal, gotArgs, gotKwargs = self.__stoneTablet.popleft()

		if gotSignal != signal:
			raise AssertionError('Unexpected signal %r, expecting %r' % (gotSignal, signal))

		# if we are evaluating QModelIndex and QPersistentModelIndex then we cannot
		# evaluate args as tuples, the items need to be evaluated individually
		if not all (x==y for x, y in zip(args, gotArgs)):
		#if args != gotArgs:
			raise AssertionError('Unexpected args %r for signal %r, expecting %r' % (gotArgs, signal, args))

		if gotKwargs != kwargs:
			raise AssertionError('Unexpected kwargs %r for signal %r, expecting %r' % (gotKwargs, signal, kwargs))

		if widget is not None and widget != gotWidget:
			raise AssertionError('Unexpected widget %r for signal %r, expecting %r' % (gotWidget, signal, widget))

	def _recordSignal(self, widget, signal, args, kwargs):
		if self._showTracer:
			self._printSignal(widget, signal, args, kwargs)

		def _mapArgs(args):
			""" Retaining QModelIndex objects is a bad idea. Really bad. So substitute these
				objects for QPersistentModelIndex equivalents.
				The equaltity operator, in expected(), will work fine, as this is overloaded
				in QPersistentModelIndex to evaluate against QModelIndex, eg
				index == QPersistentModelIndex(index)
				>>> True
			"""
			for arg in args:
				if isinstance(arg, QtCore.QModelIndex):
					yield QtCore.QPersistentModelIndex(arg)
				else:
					yield arg

		self.__stoneTablet.append((widget, signal, list(_mapArgs(args)), kwargs))

@contextmanager
def signalRecorderContext(*args, **kwargs):
	""" Context manager for SignalRecorder

		Will capture received signals to be inspected later.
		AssertionError will be raised if any signals remain in
		the queue. All signals must be removed from queue
		using expected(), or the queue cleared using reset()

		Usage::

			from mpc.pyqtUtils.utils import signalRecorderContext
			with signalRecorderContext(widget1, widget2) as recorder:
				widget1.doSomething()
				recorder.expected('mySignal()', 3, widget=widget1)
				recorder.expected('anotherSignal()', widget=widget2)
	"""
	recorder = SignalRecorder(showTracer=kwargs.get('showTracer', False))
	recorder.monitor(*args)

	yield recorder

	if not recorder.isEmpty():
		raise AssertionError('stack is not empty: %d signals left' % len(recorder))

@contextmanager
def signalTracerContext(*args):
	""" Context manager for SignalTracer

		Will output received signals to stdout

		Usage::

			from mpc.pyqtUtils.utils import signalTracerContext
			with signalTracerContext(widget1, widget2) as tracer:
				widget1.doSomething()
	"""
	tracer = SignalTracer()
	tracer.monitor(*args)
	yield tracer
