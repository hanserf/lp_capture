import zmq
import sys
import signal
import time

class ZMQStreamer_backend:
    # Start your result manager and workers before you start your producers
    def __init__(self, proto_ip, port_feed,port_worker):
        self.context = zmq.Context(1)
        # Socket facing clients
        self.frontend = self.context.socket(zmq.PULL)
        connect_to_feeder = proto_ip + ':' + port_feed
        self.frontend.bind(connect_to_feeder)

        connect_to_worker = proto_ip + ':' + port_worker
        self.backend = self.context.socket(zmq.PUSH)
        self.backend.bind(connect_to_worker)

        self.original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.exit_gracefully)
        zmq.device(zmq.STREAMER, self.frontend, self.backend)

    def exit_gracefully(self,signum, frame):
        # restore the original signal handler as otherwise evil things will happen
        # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
        signal.signal(signal.SIGINT, self.original_sigint)
        try:
            if input("\nReally quit? (y/n)> ").lower().startswith('y'):
                self.exit_zmq()
                sys.exit(1)


        except KeyboardInterrupt:
            print("Ok ok, quitting")
            self.exit_zmq()
            sys.exit(1)

        # restore the exit gracefully handler here
        signal.signal(signal.SIGINT, self.exit_gracefully)

    def exit_zmq(self):
        self.frontend.close()
        self.backend.close()
        self.context.term()


if __name__ == "__main__":
    ZMQStreamer_backend('tcp://*','5559','5560')