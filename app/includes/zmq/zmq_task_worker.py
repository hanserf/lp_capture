import sys
import time
import zmq
import random
class ZMQStreamer_backend:
    # Start your result manager and workers before you start your producers
    def __init__(self, proto_ip,port_worker):
        self.worker_id = random.randrange(1, 10005)
        print("I am worker # %s" % self.worker_id)
        self.context = zmq.Context()
        # receive work
        self.worker = self.context.socket(zmq.PULL)
        connect_to_task = proto_ip + ':' + port_worker
        self.worker.connect(connect_to_task)

    def process_data_forever(self):
        while True:
            work = self.worker.recv_json()
            data = work['num']
            result = {'worker': self.worker_id, 'payload': data}
            print("%s" % result)


if __name__ == '__main__':
    consumer = ZMQStreamer_backend('tcp://127.0.0.1','5560')
    consumer.process_data_forever()