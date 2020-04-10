"""A test that publishes NumPy arrays.
Currently the timing of this example is not accurate as it depends on the
subscriber and publisher being started at exactly the same moment. We should
use a REQ/REP side channel to synchronize the two processes at the beginning.
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
import numpy
import queue
#TODO Wrap this up in a class. Make it possible to spawn multiple publishers with topics.
#TODO Define topics in config. Topics will be signal processing related.
#TODO Subscriptions to topics and topic generation should be enabled from qtgui
import app.config as config

class ZMQ_Publisher:
    def __init__(self):
        # Socket to talk to server
        self.run_mode = config.run_mode[1]
        #self.topic = topic
        bind_to = config.zmq_setup
        self.zmq_pub_ctx = zmq.Context()
        self.array_size = 192
        self.socket = self.zmq_pub_ctx.socket(zmq.PUB)
        self.socket.bind(bind_to)
        print("Generated ZMQ Publisher")
        self.running = True

    def send_message(self,payload):
        self.socket.send_pyobj(payload)
        print("Sent single message")

    def close_connection(self):
        print('Quitting ZMQ Subscriber')
        self.socket.close()
        self.zmq_pub_ctx.destroy()

    def terminate_session(self):
        exit(0)

    def loop(self):
        print ("Waiting for subscriber to connect...")
        # We need to sleep to allow the subscriber time to connect
        time.sleep(1.0)
        print ("   Done.")
        print ("Entring run mode %s" % self.run_mode)
        if self.running == True:
            try:
                while True:
                    a = numpy.random.rand(self.array_size)
                    self.send_message(a)
                    time.sleep(0.2)

            except KeyboardInterrupt:
                print('Quitting ZMQ Subscriber')
                self.close_connection()
                self.terminate_session()
        else:
            print("Not explositly set to run")
            exit(0)


if __name__ == "__main__":
    zmqtest = ZMQ_Publisher()
    for i in range(20):
        zmqtest.send_message()
        time.sleep(0.5)
    zmqtest.close_connection()
    zmqtest.terminate_session()
    #zmqtest.loop()