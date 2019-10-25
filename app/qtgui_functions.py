from PyQt5 import QtCore, QtWidgets, uic
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import numpy as np
import time
import os
import queue
import datetime as dt
import app.config as config
from collections import deque
import zmq

class QTGuiFunctions(QtWidgets.QMainWindow):

    def __init__(self, config,  *args, **kwargs ):
        super(QTGuiFunctions, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        self.start_time = self.get_current_time()
        self.samp_rate=config.sample_rate
        self.rms_window_len =config.rms_window
        duration = config.t_stop - config.t_start
        num_points = self.get_num_points_in_plot(duration,self.samp_rate)
        t_plot =np.linspace(config.t_start, config.t_stop, num=num_points, endpoint=True, retstep=False, dtype=None, axis=0)
        self.graphWidget.setBackground('w')
        data = np.zeros(num_points)
        self.graphWidget.plot(t_plot,data)
    # -------------------------------------------------------------------------------------------------------------------
    #    Threading and ZMQ Connection
        self.thread = QtCore.QThread()
        self.zeromq_listener = ZeroMQSubscriber()
        self.zeromq_listener.moveToThread(self.thread)
        self.thread.started.connect(self.zeromq_listener.loop)
        self.zeromq_listener.message.connect(self.signal_received)
        QtCore.QTimer.singleShot(10, self.thread.start)

    def signal_received(self, message):
            data = message
            #print(message)
            self.refresh_plot(data)

    def closeEvent(self, event):
            self.zeromq_listener.running = False
            self.thread.quit()
            self.thread.wait()

    def refresh_plot(self,data):
        number_of_elements = len(data)
        duration = number_of_elements/config.sample_rate
        t_plot = self.return_plottime(0,duration,number_of_elements)
        self.update_plot(t_plot,data)

    def update_plot(self,t_plot,data):
        pen = pg.mkPen(color=(255, 0, 0))
        self.graphWidget.getPlotItem().clear()
        self.graphWidget.plot(t_plot, data, pen=pen)

    def return_plottime(self, start, stop, num_points):
        t_plot = np.linspace(start, stop, num=num_points, endpoint=True, retstep=False, dtype=None, axis=0)
        return t_plot

    def get_num_points_in_plot(self, duration, samp_rate):
        return int(duration*samp_rate)

    def get_current_time(self):
        return dt.datetime.now()


class ZeroMQSubscriber(QtCore.QObject):
       message = QtCore.pyqtSignal(np.ndarray)
       def __init__(self):
           QtCore.QObject.__init__(self)
           # Socket to talk to server
           connect_to = config.zmq_setup
           zmq_sub_ctx = zmq.Context()
           self.socket = zmq_sub_ctx.socket(zmq.SUB)
           self.socket.connect(connect_to)
           print(" Zmq Subscriber context generated for : %s" % connect_to)
           self.socket.setsockopt(zmq.SUBSCRIBE, b'')
           self.running = True

       def loop(self):
           while self.running:
               data_list = self.socket.recv_pyobj()
               data_numpy = np.asarray(data_list)
               self.message.emit(data_numpy)

#def main():
#    starttime = dt
#    app = QtWidgets.QApplication(sys.argv)
#    main = QTGuiFunctions(config)
#    main.update_plot()
#    main.show()
#    sys.exit(app.exec_())


#if __name__ == '__main__':
#    main()