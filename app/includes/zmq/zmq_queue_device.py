import time
import zmq
from zmq.devices.basedevice import ProcessDevice
from multiprocessing import Process
import random

frontend_port = 5559
backend_port = 5560
number_of_workers = 4

queuedevice = ProcessDevice(zmq.QUEUE, zmq.XREP, zmq.XREQ)
queuedevice.bind_in("tcp://127.0.0.1:%d" % frontend_port)
queuedevice.bind_out("tcp://127.0.0.1:%d" % backend_port)
queuedevice.setsockopt_in(zmq.RCVHWM, 1)
queuedevice.setsockopt_out(zmq.SNDHWM, 1)
queuedevice.start()
time.sleep (2)

def server(backend_port):
    print("Connecting a server to queue device")
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.connect("tcp://127.0.0.1:"+ str(backend_port))
    server_id = random.randrange(1,10005)
    while True:
        message_r = socket.recv_multipart()
        message_d = socket.recv_pyobj()
        message = {message_r,message_d}
        print ("Received request: %s" %message)
        socket.send_string("Response from ",zmq.SNDMORE)
        socket.send_pyobj(server_id)

def client(frontend_port, client_id):
    print("Connecting a worker #%s to queue device" % client_id)
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:"+str(frontend_port))
    #  Do 10 requests, waiting each time for a response
    for request in range (5):
        print("Sending request # %s" % request)
        socket.send_string("Request from client: ",zmq.SNDMORE)
        socket.send_pyobj(client_id)
        #  Get the reply.
        message_r = socket.recv_multipart()
        message_d = socket.recv_pyobj()
        message = {message_r,message_d}
        print("Received reply %s" %request + "[ %s ]" % message)


Process(target=server, args=(backend_port,)).start()

time.sleep(2)

for client_id in range(number_of_workers):
    Process(target=client, args=(frontend_port, client_id,)).start()
