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
import app.includes.config as config

class ZMQBackend:
    def __init__(self):
        self.zmq_service_ip=config.zmq_proto_ip
        self.zmq_context = zmq.Context()
        self.zmq_pubsub_port = config.zmq_port_pubsub
        self.publisher = 0
        self.zmq_reqrep_port = config.zmq_port_reqrep
        self.reply_server = ZMQReply(context=self.zmq_context,proto_ip=self.zmq_service_ip,port=self.zmq_reqrep_port)

    def __str__(self):
        return ",".join(["{}:{} ".format(k, v) for k, v in self.__dict__.items()])

    __repr__ = __str__

    def decode_request(self,request):
        if request == "START_PUB":
            self.init_publisher()


    def init_publisher(self):
        self.publisher = ZMQPublisher(context=self.zmq_context, proto_ip=self.zmq_service_ip, port=self.zmq_pubsub_port)

class ZMQPublisher:
    def __init__(self,context, proto_ip,port):
        # Socket to talk to server
        self.run_mode = config.run_mode[1]
        self.topics_dict = {"dummy_entry":0}
        bind_to = proto_ip + ':' + port
        self.zmq_pub_ctx = context
        self.socket = self.zmq_pub_ctx.socket(zmq.PUB)
        self.socket.bind(bind_to)
        print("Generated ZMQ Publisher: %s" %self.zmq_backend)
        #Control
        self.running = False
        self.armed  = True


    def __str__(self):
        return ",".join(["{}:{} ".format(k, v) for k, v in self.__dict__.items()])

    __repr__ = __str__

    def send_message(self,topic, payload):
        self.socket.send_string(topic, zmq.SNDMORE)
        self.socket.send_pyobj(payload)
        print("Sent single message")

    def set_state_running(self):
        self.running = True

    def close_connection(self):
        print('Quitting ZMQ Publisher')
        self.socket.close()
        self.zmq_pub_ctx.destroy()

    def terminate_session(self):
        exit(0)

    def publish_all_topics_list(self):
        for topic in self.zmq_backend.topics_dict:
            self.socket.send_pyobj(str(topic), flags=zmq.SNDMORE)
            self.socket.send_pyobj(self.topics_dict[topic])
            time.sleep(1e-5)

    def publish_topic(self,topic):
        self.socket.send_pyobj(str(topic),flags=zmq.SNDMORE)
        self.socket.send_pyobj(self.topics_dict.get(topic))

    def delete_topic(self,topic):
        del self.topics_dict[topic]

    def add_topic(self, topic_key, topic_value):
        self.topics_dict.update({topic_key: topic_value})




class ZMQReply:
    def __init__(self,context,proto_ip,port):
        # Socket to talk to server
        bind_to = proto_ip + ':' + port
        self.zmq_rep_ctx = context
        self.socket = self.zmq_rep_ctx.socket(zmq.REP)
        self.socket.bind(bind_to)
        print("Generated ZMQ Reply Server")

    def send_message(self,message):
        print("REPLY: %s" % message)
        self.socket.send(message)

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



def main():
    backend = ZMQBackend()
    print("Initialized service, waiting for client connection")
    while(1):
        request = backend.reply_server.receive_message()
        backend.decode_request(request)


if __name__ == "__main__":
    main()