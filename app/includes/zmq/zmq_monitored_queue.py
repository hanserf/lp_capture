import time
import zmq
from zmq.devices.basedevice import ProcessDevice
from zmq.devices.monitoredqueuedevice import MonitoredQueue
from zmq.utils.strtypes import asbytes
from multiprocessing import Process
import random

frontend_port = 5559
backend_port = 5560
monitor_port = 5562
number_of_workers = 2


def monitordevice():
    in_prefix = asbytes('in')
    out_prefix = asbytes('out')
    monitoringdevice = MonitoredQueue(zmq.XREP, zmq.XREQ, zmq.PUB, in_prefix, out_prefix)

    monitoringdevice.bind_in("tcp://127.0.0.1:"+ str(frontend_port))
    monitoringdevice.bind_out("tcp://127.0.0.1:" + str(backend_port))
    monitoringdevice.bind_mon("tcp://127.0.0.1:" + str(monitor_port))

    monitoringdevice.setsockopt_in(zmq.HWM, 1)
    monitoringdevice.setsockopt_out(zmq.HWM, 1)
    monitoringdevice.start()
    print("Program: Monitoring device has started")

def server(backend_port):
    print("Program: Server connecting to device")
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.connect("tcp://127.0.0.1:" + str(backend_port))
    server_id = random.randrange(1, 10005)
    while True:
        message = socket.recv_string()
        print("Server: Received -" + message)
        socket.send_multipart("Response from server #")
        socket.send_pyobj(server_id)

def client(frontend_port, client_id):
    print "Program: Worker #%s connecting to device" % client_id
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:" + str(frontend_port))
    request_num = 1
    msg = "Request #"+ str(request_num) + " from client#" + str(client_id)
    socket.send_string(msg)
    #  Get the reply.
    message = socket.recv_multipart()
    print "Client: Received - %s" % message

def monitor():
    print "Starting monitoring process"
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    print "Collecting updates from server..."
    socket.connect ("tcp://127.0.0.1:%s" % monitor_port)
    socket.setsockopt(zmq.SUBSCRIBE, "")
    while True:
        string = socket.recv_multipart()
        print "Monitoring Client: %s" % string


monitoring_p = Process(target=monitordevice)
monitoring_p.start()
server_p = Process(target=server, args=(backend_port,))
server_p.start()
monitorclient_p = Process(target=monitor)
monitorclient_p.start()
time.sleep(2)

for client_id in range(number_of_workers):
    Process(target=client, args=(frontend_port, client_id,)).start()

time.sleep(10)
server_p.terminate()
monitorclient_p.terminate()
monitoring_p.terminate()