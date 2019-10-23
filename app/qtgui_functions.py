from PyQt5 import QtWidgets, uic
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import numpy as np
import os
import datetime as dt
import app.config as config
from collections import deque

class QTGuiFunctions(QtWidgets.QMainWindow):

    def __init__(self, config, *args, **kwargs ):
        super(QTGuiFunctions, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        self.start_time = self.get_current_time()
        self.samp_rate=config.sample_rate
        self.rms_window_len =config.rms_window
        self.duration = config.t_stop - config.t_start
        self.num_points = self.get_num_points_in_plot(self.duration,self.samp_rate)
        self.t_plot = self.set_plottime(config.t_start,config.t_stop,self.num_points)
        self.graphWidget.setBackground('w')

    def update_plot(self,time,data):
        pen = pg.mkPen(color=(255, 0, 0))
        self.graphWidget.plot(time, data, pen=pen)

    def set_plottime(self, start, stop, num_points):
        return np.linspace(start, stop, num=num_points, endpoint=True, retstep=False, dtype=None, axis=0)

    def get_num_points_in_plot(self, duration, samp_rate):
        return int(duration/samp_rate)

    def get_current_time(self):
        return dt.datetime.now()

def main():
    starttime = dt
    app = QtWidgets.QApplication(sys.argv)
    main = QTGuiFunctions(config)
    main.update_plot()
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()