import time
import zmq
from zmq.devices.basedevice import ProcessDevice
from multiprocessing import Process

frontend_port = 5559
backend_port = 5560
number_of_workers = 16

streamerdevice  = ProcessDevice(zmq.STREAMER, zmq.PULL, zmq.PUSH)

streamerdevice.bind_in("tcp://127.0.0.1:" + str(frontend_port))
streamerdevice.bind_out("tcp://127.0.0.1:"+ str(backend_port))
streamerdevice.setsockopt_in(zmq.IDENTITY, b"PULL")
streamerdevice.setsockopt_out(zmq.IDENTITY, b"PUSH")

streamerdevice.start()


def server():
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://127.0.0.1:" + str(frontend_port))

    for i in range(100000):
        msg = '#' + str(i)
        socket.send_pyobj(msg)


def worker(work_num):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.connect("tcp://127.0.0.1:" + str(backend_port))

    while True:
        message = socket.recv_pyobj()
        print("Worker #"+str(work_num) + " got message! %s" %message)
        time.sleep(1e-3)


for work_num in range(number_of_workers):
    Process(target=worker, args=(work_num,)).start()
time.sleep(1)

server()
