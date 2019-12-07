
import sys
import time
import random
import zmq
import numpy as np
import itertools
import queue
#TODO Subscriptions to topics and topic generation should be enabled from qtgui
import config as config


class ZMQBackend:
    def __init__(self):
        self.zmq_service_ip = config.zmq_proto_ip
        self.zmq_context = zmq.Context()
        self.zmq_pubsub_port = config.zmq_port_pubsub
        self.zmq_reqrep_port = config.zmq_port_reqrep
        self.reply_server = ZMQReply(context=self.zmq_context, proto_ip=self.zmq_service_ip, port=self.zmq_reqrep_port)
        self.publisher = ZMQPublisher(context=self.zmq_context, proto_ip=self.zmq_service_ip, port=self.zmq_pubsub_port)
        print("Zmq Backend initialized")

    def __str__(self):
        return ",".join(["{}:{} ".format(k, v) for k, v in self.__dict__.items()])

    __repr__ = __str__

    def connect_to_master(self):
        print("Waiting for request:")
        self.reply_server.connect_to_outside()



class ZMQPublisher:
    def __init__(self,context, proto_ip,port):
        # Socket to talk to server
        self.run_mode = config.run_mode[1]
        self.topics_dict = {}
        bind_to = proto_ip + ':' + port
        self.zmq_pub_ctx = context
        self.socket = self.zmq_pub_ctx.socket(zmq.PUB)
        self.socket.bind(bind_to)
        print("Generated ZMQ Publisher:")


    def __str__(self):
        return ",".join(["{}:{} ".format(k, v) for k, v in self.__dict__.items()])

    __repr__ = __str__

    def send_message(self,topic, payload):
        self.socket.send_string(topic, zmq.SNDMORE)
        self.socket.send_pyobj(payload)
        print("Sent single message")

    def close_connection(self):
        print('Quitting ZMQ Publisher')
        self.socket.close()
        self.zmq_pub_ctx.destroy()

    def terminate_session(self):
        exit(0)

    def publish_all_topics_list(self):
        for topic in self.topics_dict:
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

    def refresh_topic(self,topic,data):
        self.topics_dict[topic] = data



class ZMQReply:
    def __init__(self,context,proto_ip,port):
        # Socket to talk to server
        bind_to = proto_ip + ':' + port
        self.zmq_rep_ctx = context
        self.socket = self.zmq_rep_ctx.socket(zmq.REP)
        self.socket.bind(bind_to)
        print("Generated ZMQ Reply Server")

    def connect_to_outside(self):
        conn = self.receive_request()
        self.send_message("Datalogger Alive")

    def send_message(self,message):
        print("REPLY: %s" % message)
        self.socket.send_string(message)

    def receive_request(self):
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
    debug_writer = ZMQBackend()
    debug_writer.connect_to_master()
    n_iterations = 100
    data = np.random.normal(size=20)
    topic = "random_numbers"
    debug_writer.publisher.send_message(topic, data)

    for i in range(n_iterations):
        print("Publishing number %d" %i)
        debug_writer.publisher.publish_topic("random_numbers")
        time.sleep(1/50)
        data = np.random.normal(size=20)
        debug_writer.publisher.send_message(topic,data)

if __name__ == "__main__":
    main()