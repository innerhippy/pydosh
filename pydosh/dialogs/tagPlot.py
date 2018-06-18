from PyQt5 import QtCore, QtWidgets
import pdb
import itertools
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from pydosh.ui_tagPlot import Ui_TagPlot

class TagPlot(Ui_TagPlot, QtWidgets.QDialog):
    def __init__(self, data, parent=None):
        super(TagPlot, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)
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
        for tag, values in data.iteritems():
            df = pd.DataFrame(values, columns=['date', 'amount'])
            df.date = pd.to_datetime(df.date)
            df = df.set_index('date').resample('M', how='sum').interpolate()
            line, = ax.plot(df, '%s-' % cols.next())
            legend.append((line, tag))

        # Find the lowest number for the plot
        all_values = [v[1] for v in itertools.chain.from_iterable(data.itervalues())]
        print min(all_values), max(all_values)
        y_lim = 0 if min(all_values) > 0 else min(all_values)
        ax.set_ylim(bottom=y_lim, top=max(all_values)+10)

        if len(legend) > 1:
            ax.set_title('Tag time series')
            x, y = zip(*legend)
            self.figure.legend(x, y)
        else:
            ax.set_title(tag)

        self.figure.autofmt_xdate()
        self.draw()
