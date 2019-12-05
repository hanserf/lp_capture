from PyQt5 import QtCore, QtWidgets, uic
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import time
import os
import queue
import datetime as dt
import config as config
import numpy as np
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
        self.zmq_context = zmq.Context()
        self.zmq_service_ip = config.zmq_proto_ip
        self.zmq_pubsub_port = config.zmq_port_pubsub
        self.zmq_reqrep_port = config.zmq_port_reqrep
        self.zmq_request = ZMQRequest(context=self.zmq_context, proto_ip=self.zmq_service_ip, port=self.zmq_reqrep_port)
        goahead = self.zmq_request.probe_connection("Please connect to me")
        #self.zmq_request.close_connection()
        # -------------------------------------------------------------------------------------------------------------------
        #    Threading and ZMQ Connection
        print("Goahead Received :%s",goahead)
        self.thread = QtCore.QThread()
        self.zeromq_listener = ZMQSubscriber(context=self.zmq_context, proto_ip=self.zmq_service_ip, port=self.zmq_pubsub_port)
        self.zeromq_listener.moveToThread(self.thread)
        self.thread.started.connect(self.zeromq_listener.loop)
        self.zeromq_listener.message.connect(self.signal_received)
        #QtCore.QTimer.singleShot(10, self.thread.start)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200)  # in milliseconds
        self.timer.start()
        self.timer.timeout.connect(self.thread.start)


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


class ZMQSubscriber(QtCore.QObject):
       message = QtCore.pyqtSignal(np.ndarray)
       def __init__(self,context, proto_ip,port):
           QtCore.QObject.__init__(self)
           # Socket to talk to server
           connect_to = proto_ip + ':' + port
           self.zmq_sub_ctx = context
           self.socket = self.zmq_sub_ctx.socket(zmq.SUB)
           self.socket.connect(connect_to)
           print(" Zmq Subscriber context generated for : %s" % connect_to)
           self.socket.setsockopt(zmq.SUBSCRIBE, b"random_numbers")
           self.running = True

       def zmq_get_subscription(self):
           topic = self.socket.recv()
           print("TOPIC : %s" % topic)
           data_list = self.socket.recv_pyobj()
           data_numpy = np.asarray(data_list)
           self.message.emit(data_numpy)

       def loop(self):
           print("Entering ZMQ Listening Loop ")
           while (1):
               topic = self.socket.recv()
               print("TOPIC : %s" %topic)
               data_list = self.socket.recv_pyobj()
               data_numpy = np.asarray(data_list)
               self.message.emit(data_numpy)
               time.sleep(1/30
                          )

class ZMQRequest:
    def __init__(self,context, proto_ip,port):
        # Socket to talk to server
        connect_to = proto_ip + ':' + port
        self.zmq_req_ctx = context
        self.socket = self.zmq_req_ctx.socket(zmq.REQ)
        self.socket.connect(connect_to)
        print("Generated ZMQ Request Server")

    def probe_connection(self,tx_message):
        print("Sending request: %s" % tx_message)
        self.socket.send_string(tx_message)
        rx_message = self.socket.recv()
        print("Received reply %s"% rx_message)
        return rx_message

    def close_connection(self):
        print('Quitting ZMQ Request')
        self.socket.close()
        self.zmq_req_ctx.destroy()

    def terminate_session(self):
        exit(0)

def main():
    starttime = dt
    app = QtWidgets.QApplication(sys.argv)
    main = QTGuiFunctions(config)
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()