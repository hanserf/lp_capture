"""A test that publishes NumPy arrays.
This application uses a ZMQ REQ REP Sidechannel for a Publish subscribe pattern for numpy.ndarrays
The publisher is a reply server setting up topics to be published withing the context of the application.
The REQ REP Sidechannel will be a control interface to enable disable topics.
A Custom class has been made to glue the two ZMQ Class instances into a lightweigh hackable interface to any application
"""
#
#    Copyright (c) 2010 Brian E. Granger
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import time
import random
import zmq
import numpy as np
import itertools
import queue
#TODO Wrap this up in a class. Make it possible to spawn multiple publishers with topics.
#TODO Define topics in config. Topics will be signal processing related.
#TODO Subscriptions to topics and topic generation should be enabled from qtgui
import app.config as config

class CapturePackage:
    def __init__(self, samp_rate, n_samples):
        self.samp_rate = samp_rate
        self.n_samp = n_samples
        self.capture_time = self.set_capture_time()
        self.l_raw_data = np.zeros(self.n_samp)
        self.r_raw_data = np.zeros(self.n_samp)
        self.l_fft_data = np.zeros(self.n_samp)
        self.r_fft_data = np.zeros(self.n_samp)
        self.modes = []
        self.modes.append("Stereo")
        self.modes.append("Mono")

    def __str__(self):
        return ",".join(["{}:{} ".format(k, v) for k, v in self.__dict__.items()])

    __repr__ = __str__

    def set_capture_time(self):
        self.capture_time = self.n_samples * self.samp_rate


class ZMQBackend:
    def __init__(self, running, armed, topics, processing):
        self.running = running
        self.armed = armed
        self.topics_list = topics
        self.capture_enable=processing[0]
        self.fft_enable = processing[1]
        self.zmq_service_ip=config.zmq_proto_ip
        self.zmq_context = zmq.Context()
    def __str__(self):
        return ",".join(["{}:{} ".format(k, v) for k, v in self.__dict__.items()])

    __repr__ = __str__

    def check_running(self):
        return self.running

    def set_running(self):
        self.running = True

    def check_armed(self):
        return self.armed

    def set_armed(self):
        self.armed = True


class ZMQPublisher:
    def __init__(self,PORT):
        # Socket to talk to server
        self.run_mode = config.run_mode[1]
        #self.topic = topic
        self.zmq_backend = ZMQBackend(running=False,armed=True,topics_list=config.zmq_topics_list)
        bind_to = self.zmq_backend.zmq_service_ip + ':' + PORT
        self.zmq_pub_ctx = self.zmq_backend.zmq_context
        self.socket = self.zmq_pub_ctx.socket(zmq.PUB)
        self.socket.bind(bind_to)
        print("Generated ZMQ Publisher: %s" %self.zmq_backend)
        self.running = self.zmq_backend.check_running()
        self.armed  = self.zmq_backend.check_armed()
        # Initializing results structure
        self.data_capture = CapturePackage(samp_rate=config.sample_rate, n_samples=config.packet_size)


    def __str__(self):
        return ",".join(["{}:{} ".format(k, v) for k, v in self.__dict__.items()])

    __repr__ = __str__

    def send_message(self,topic, payload):
        self.socket.send_string(topic, zmq.SNDMORE)
        self.socket.send_pyobj(payload)
        print("Sent single message")

    def generate_random_data(self):
        a = np.random.rand(self.num)

    def send_timeseries(self):
        self.send_message(self.data_capture.r_fft_data)


    def close_connection(self):
        print('Quitting ZMQ Subscriber')
        self.socket.close()
        self.zmq_pub_ctx.destroy()

    def terminate_session(self):
        exit(0)

    def publish_all_topics_list(self):
        msg_counter = itertools.count()
        try:
            for topic in itertools.cycle(self.zmq_backend.topics_list):
                msg_body = str(msg_counter.next())
                print('ZMQ_PUBLISHER_TOPICS : %s,' % (topic, msg_body))
                self.socket.send_pyobj(topic)
                time.sleep(0.01)
        except KeyboardInterrupt:
            pass


    def loop(self):
        print ("Entring run mode %s" % self.run_mode)
        while self.running == True:

            self.send_message(a)
            time.sleep(0.2)



class ZMQReply:
    def __init__(self,PORT):
        # Socket to talk to server
        self.run_mode = config.run_mode[1]
        self.zmq_backend = ZMQBackend()
        bind_to = config.zmq_proto_ip + ':' + PORT
        self.zmq_rep_ctx = zmq.Context()
        self.array_size = 192
        self.socket = self.zmq_rep_ctx.socket(zmq.REP)
        self.socket.bind(bind_to)
        print("Generated ZMQ Reply Server")
        self.running = True
        self.armed = True

    def stop_running(self):
        self.running = False

    def start_running(self):
        self.running = True

    def send_message(self,message):
        print("REPLY: %s" % message)
        self.socket.send(message)

    def state_decoder(self,message):
        if message == 'run':
            self.start_running()

    def receive_message(self):
        message = self.socket.recv()
        print("REQ : %s" % message)
        return message

    def close_connection(self):
        print('Quitting ZMQ Reply')
        self.socket.close()
        self.zmq_rep_ctx.destroy()

    def terminate_session(self):
        exit(0)




def zmq_pub_testfun(num_messages,interval_s):


    for i in range(num_messages):
        a = numpy.random.rand(zmqtest.array_size)
        zmqtest.send_message(a)
        time.sleep(interval_s)
    zmqtest.close_connection()
    zmqtest.terminate_session()

def main()
    zmq_pub_testfun(20, 0.5)


if __name__ == "__main__":
    main()