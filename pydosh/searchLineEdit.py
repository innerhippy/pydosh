from PyQt4 import QtGui, QtCore

class SearchLineEdit(QtGui.QLineEdit):
	controlKeyPressed = QtCore.pyqtSignal(int)

	def __init__(self, parent=None):
		super(SearchLineEdit, self).__init__(parent=parent)
		
		clearButton = QtGui.QToolButton(self)
#		clearButton
"""
	QLineEdit(parent)
{
	clearButton = new QToolButton(this);
	QPixmap pixmap = QPixmap(":/icons/clearsearch.png").scaledToHeight(15, Qt::SmoothTransformation);
	clearButton->setIcon(QIcon(pixmap));
	clearButton->setIconSize(pixmap.size());
	clearButton->setCursor(Qt::ArrowCursor);
	clearButton->setStyleSheet("QToolButton { border: none; padding: 0px; }");
	clearButton->hide();
	connect(clearButton, SIGNAL(clicked()), this, SLOT(clear()));
	connect(this, SIGNAL(textChanged(const QString&)), this, SLOT(updateCloseButton(const QString&)));
	int frameWidth = style()->pixelMetric(QStyle::PM_DefaultFrameWidth);
	setStyleSheet(QString("QLineEdit { padding-right: %1px; } ").arg(clearButton->sizeHint().width() + frameWidth + 1));
	QSize msz = minimumSizeHint();
	setMinimumSize(qMax(msz.width(), clearButton->sizeHint().height() + frameWidth * 2 + 2),
			qMax(msz.height(), clearButton->sizeHint().height() + frameWidth * 2 + 2));
}

void SearchLineEdit::keyPressEvent(QKeyEvent *event) 
{
	if (event->key() == Qt::Key_Space) {
		emit controlKeyPressed(event->key());
	}
	QLineEdit::keyPressEvent(event);
}

void SearchLineEdit::resizeEvent(QResizeEvent *)
{
	QSize sz = clearButton->sizeHint();
	int frameWidth = style()->pixelMetric(QStyle::PM_DefaultFrameWidth);
	clearButton->move(rect().right() - frameWidth - sz.width(),
			(rect().bottom() + 1 - sz.height())/2);
}

void SearchLineEdit::updateCloseButton(const QString& text)
{
	clearButton->setVisible(!text.isEmpty());
}

void SearchLineEdit::paintEvent(QPaintEvent *event)
{
	QLineEdit::paintEvent(event);
	if (text().isEmpty() && !hasFocus()) {
		QPixmap pixmap = QPixmap(":/icons/search.png").scaledToHeight(15, Qt::SmoothTransformation);
		QRect r(QPoint(0, 0), pixmap.size());
		r.moveCenter(QPoint(pixmap.width()/2 +4, rect().center().y()));
		QPainter painter(this);
		painter.drawPixmap(r, pixmap);
	}
}
"""
