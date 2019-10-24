from PyQt5 import QtCore, QtWidgets, uic
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import numpy as np
import os
import datetime as dt
import app.config as config
from collections import deque
import zmq

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
        self.t_plot =np.linspace(config.t_start, config.t_stop, num=self.num_points, endpoint=True, retstep=False, dtype=None, axis=0)
        self.graphWidget.setBackground('w')
        self.data = np.zeros(self.num_points)
        self.graphWidget.plot(self.t_plot,self.data)
    # -------------------------------------------------------------------------------------------------------------------
    #   ZMQ context for gui data subscription
        self.zmq_sub_context = 0
    # -------------------------------------------------------------------------------------------------------------------
    #   ZMQ context for gui data subscription
        self.zmq_queue = 0
    #-------------------------------------------------------------------------------------------------------------------
    #    Timer functions for real time updates
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(self.duration*1000)  # in milliseconds
        self.timer.start()
        self.timer.timeout.connect(self.refresh_plot)
        self.plotItem = self.addPlot(title="Recording: Signal")
        self.plotDataItem = self.plotItem.plot([], pen=None,
                                               symbolBrush=(255, 0, 0), symbolSize=5, symbolPen=None)

    def init_zmq_sub_context(self):
        connect_to = config.zmq_setup
        ctx = zmq.Context()
        s = ctx.socket(zmq.SUB)
        s.connect(connect_to)
        print(" Zmq Subscriber context generated for : %s" % connect_to)
        s.setsockopt(zmq.SUBSCRIBE, b'')
        return s

    def zmq_receive(self):
        data_list = self.zmq_sub_context.recv_pyobj()
        data_2Dnumpy = np.asarray(data_list)
        self.data = self.flatten1D(data_2Dnumpy)

    def flatten1D(array_2d):
        N_dim, M_dim = array_2d.shape
        O_dim = N_dim * M_dim
        return array_2d.reshape(O_dim)

    def refresh_plot(self,input_data):
        self.set_data(input_data=input_data)
        number_of_elements = len(input_data)
        duration = number_of_elements/config.sample_rate
        self.set_plottime(0,duration,number_of_elements)
        self.start_time = self.get_current_time()
        self.update_plot(input_data)

    def set_data(self,input_data):
        self.data=input_data

    def update_plot(self):
        pen = pg.mkPen(color=(255, 0, 0))
        self.graphWidget.plot(self.t_plot, self.data, pen=pen)

    def set_plottime(self, start, stop, num_points):
        self.t_plot = np.linspace(start, stop, num=num_points, endpoint=True, retstep=False, dtype=None, axis=0)


    def get_num_points_in_plot(self, duration, samp_rate):
        return int(duration/samp_rate)

    def get_current_time(self):
        return dt.datetime.now()


    def get_plottime(self):
        return self.t_plot






class MyWidget(pg.GraphicsWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100) # in milliseconds
        self.timer.start()
        self.timer.timeout.connect(self.onNewData)

        self.plotItem = self.addPlot(title="Lidar points")

        self.plotDataItem = self.plotItem.plot([], pen=None,
            symbolBrush=(255,0,0), symbolSize=5, symbolPen=None)


    def setData(self, x, y):
        self.plotDataItem.setData(x, y)


    def onNewData(self):
        numPoints = 1000
        x = np.random.normal(size=numPoints)
        y = np.random.normal(size=numPoints)
        self.setData(x, y)

#def main():
#    starttime = dt
#    app = QtWidgets.QApplication(sys.argv)
#    main = QTGuiFunctions(config)
#    main.update_plot()
#    main.show()
#    sys.exit(app.exec_())


#if __name__ == '__main__':
#    main()