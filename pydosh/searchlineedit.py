from PyQt4 import QtGui, QtCore
import pydosh_rc

class SearchLineEdit(QtGui.QLineEdit):
	controlKeyPressed = QtCore.pyqtSignal(int)
	clearButtonPressed = QtCore.pyqtSignal()
	editingFinshed = QtCore.pyqtSignal('QString')

	def __init__(self, parent=None):
		super(SearchLineEdit, self).__init__(parent=parent)

		clearButton = QtGui.QToolButton(self)
		pixmap = QtGui.QPixmap(":/icons/clearsearch.png").scaledToHeight(15, QtCore.Qt.SmoothTransformation)
		clearButton.setIcon(QtGui.QIcon(pixmap))
		clearButton.setIconSize(pixmap.size())
		clearButton.setCursor(QtCore.Qt.ArrowCursor)
		clearButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")
		clearButton.hide()

		clearButton.clicked.connect(self.clear)
		clearButton.clicked.connect(self.clearButtonPressed.emit)
		self.textChanged.connect(self.updateCloseButton)

		frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
		self.setStyleSheet(QtCore.QString("QLineEdit { padding-right: %1px; } ").arg(clearButton.sizeHint().width() + frameWidth + 1))

		self.clearButton = clearButton

		self.textChanged.connect(self._textChanged)
		self._timer = QtCore.QTimer()
		self._timer.setSingleShot(True)
		self._timer.timeout.connect(self._emitChanges)
		self.__delay = None

	def setDelay(self, delay):
		""" Sets the time delay to trigger the editingFinshed signal after the 
			line edit has received user input.
		"""
		self.__delay = delay

	def _textChanged(self, text):
		if self.__delay:
			if self._timer.isActive():
				self._timer.stop()
			self._timer.start(self.__delay)
		else:
			self._emitChanges()

	def _emitChanges(self):
		""" Slot to emit the editingFinished signal containg the
			current edit text
		"""
		self.editingFinshed.emit(self.text())

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Space:
			self.controlKeyPressed.emit(event.key())
		super(SearchLineEdit, self).keyPressEvent(event)

	def resizeEvent(self, event):
		sz = self.clearButton.sizeHint()
		frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
		self.clearButton.move(self.rect().right() - frameWidth - sz.width(),
			(self.rect().bottom() + 1 - sz.height())/2)

	def updateCloseButton(self, text):
		self.clearButton.setVisible(not text.isEmpty())

	def paintEvent(self, event):
		super(SearchLineEdit, self).paintEvent(event)
		if not self.text() and not self.hasFocus():
			pixmap = QtGui.QPixmap(":/icons/search.png").scaledToHeight(15, QtCore.Qt.SmoothTransformation)
			rect = QtCore.QRect(QtCore.QPoint(0, 0), pixmap.size())
			rect.moveCenter(QtCore.QPoint(pixmap.width()/2 +4, self.rect().center().y()))
			painter = QtGui.QPainter(self)
			painter.drawPixmap(rect, pixmap)
