from PyQt5 import QtCore, QtWidgets
import itertools
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from pydosh.ui_tagPlot import Ui_TagPlot

class TagPlot(Ui_TagPlot, QtWidgets.QDialog):
    def __init__(self, data, dark=False, parent=None):
        super(TagPlot, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)

        if dark:
            import matplotlib.pyplot as plt
            plt.style.use('dark_background')

        self.plt = PlotCanvas(data, parent=self.canvas)
        self.resize(1000, 600)
        self.setWindowTitle('Monthly summary')

    def resizeEvent(self, event):
        self.plt.setGeometry(self.canvas.rect())

class PlotCanvas(FigureCanvas):

    def __init__(self, data, parent=None):
        super(PlotCanvas, self).__init__(Figure(dpi=100))
        self.axes = self.figure.add_subplot(111)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        if data:
            self.plot(data)

    def plot(self, data):
        cols = itertools.chain('b', 'g', 'r', 'c', 'm', 'y', 'k')
        legend = []
        import pandas as pd
        ax = self.figure.add_subplot(111)
        y_mins = set()
        y_maxs = set()
        for tag, values in data.iteritems():
            df = pd.DataFrame(values, columns=['date', 'amount'])
            df.date = pd.to_datetime(df.date)
            df = df.set_index('date')
            resampled = df.resample('M', how='sum').interpolate()
            line, = ax.plot(resampled, '%s-' % cols.next())
            legend.append((line, tag))
            y_mins.add(min(resampled.amount))
            y_maxs.add(max(resampled.amount))

        y_min = min(y_mins) if min(y_mins) < 0 else 0
        y_max = max(y_maxs) * 1.1
        ax.set_ylim(bottom=y_min, top=y_max)

        if len(legend) > 1:
            ax.set_title('Tag time series')
            x, y = zip(*legend)
            self.figure.legend(x, y)
        else:
            ax.set_title(tag)

        self.figure.autofmt_xdate()
        self.draw()
