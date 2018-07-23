from PyQt5 import QtCore, QtWidgets
import logging
import itertools
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
try:
    import pandas as pd
    import numpy as np
except ImportError:
    pass

from pydosh.ui_recPlot import Ui_RecPlot


class RecPlot(Ui_RecPlot, QtWidgets.QDialog):
    def __init__(self, data, dark=False, parent=None):
        super(RecPlot, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.aggregateButton.setChecked(False)

        if dark:
            import matplotlib.pyplot as plt
            plt.style.use('dark_background')

        self.plt = PlotCanvas(data, parent=self.canvas)
        self.aggregateButton.clicked.connect(self.plt.setAggregate)
        self.resize(1000, 600)
        self.setWindowTitle('Monthly summary')

    def resizeEvent(self, event):
        self.plt.setGeometry(self.canvas.rect())


class PlotCanvas(FigureCanvas):

    def __init__(self, data, parent=None):
        super(PlotCanvas, self).__init__(Figure(dpi=100))
        self.axes = self.figure.add_subplot(111)
        self.setParent(parent)
        self._data = data
        self._useAggregate = False

        FigureCanvas.setSizePolicy(self,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.plot()

    def setAggregate(self, aggregate):
        self._useAggregate = aggregate
        self.plot()

    def _trend(self, df):
        coefficients, residuals, _, _, _ = np.polyfit(range(len(df.index)), df, 1, full=True)
        trend = [coefficients[0] * x + coefficients[1] for x in range(len(df))]
        return pd.DataFrame(trend, df.index)

    def guessFrequency(self):
        dates = list(itertools.chain.from_iterable(self._data.itervalues()))
        min_date,_= min(dates, key=lambda x: x[0])
        max_date,_= max(dates, key=lambda x: x[0])
        days = (max_date - min_date).total_seconds()/(60*60*24)
        if days <= 7:
            return 'D'
        elif days <=31:
            return 'W'
        elif days <=365:
            return 'M'
        return 'Y'

    def _getData(self):
        if self._useAggregate:
            return {
                'Aggregate': list(itertools.chain.from_iterable(self._data.itervalues()))
            }
        else:
            return self._data

    def plot(self):
        cols = itertools.cycle(['b', 'g', 'r', 'c', 'm', 'y', 'k'])
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        y_mins = set()
        y_maxs = set()
        legend = []

        freq = self.guessFrequency()
        data = self._getData()

        if not data:
            return

        for tag, values in data.iteritems():
            df = pd.DataFrame(sorted(values), columns=['date', 'amount'])
            df.date = pd.to_datetime(df.date)
            df = df.set_index('date')
            resampled = df.resample(freq, how='sum').interpolate()
            col = cols.next()
            plot_type = '-' if len(values) > 1 else 'o'
            line, = ax.plot(resampled, col+plot_type)
            legend.append((line, '{} (avg {})'.format(tag, int(resampled.amount.mean()))))
            y_mins.add(min(resampled.amount))
            y_maxs.add(max(resampled.amount))

            ax.plot(self._trend(resampled), '%s:' % col)

        y_min = min(y_mins) if min(y_mins) < 0 else 0
        y_max = max(y_maxs) * 1.1
        ax.set_ylim(bottom=y_min, top=y_max)

        if len(legend) == 1:
            ax.set_title(legend[0][1])
        else:
            ax.set_title('Tag time series')
            x, y = zip(*legend)
            self.figure.legend(x, y)

        self.figure.autofmt_xdate()
        self.draw()
