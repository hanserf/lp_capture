import time
import zmq
import app.includes.config as config


class ZMQProducer:
    # Start your result manager and workers before you start your producers
    def __init__(self, proto_ip, port_feed):
        # Socket to talk to server
        connect_to = proto_ip + ':' + port_feed
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.connect(connect_to)
        print("Generated ZMQ Push producer")

    def produce_message(self,header,payload):
        work_message = { header : payload }
        self.socket.send_json(work_message)


if __name__ == '__main__':
    producer = ZMQProducer(proto_ip=config.zmq_proto_ip, port_feed=config.zmq_port_producer_streamer)
    # Start your result manager and workers before you start your producers
    for num in range(100000):
        header = 'num'
        payload = num
        producer.produce_message(header,payload)
        time.sleep(1 / 10000)
