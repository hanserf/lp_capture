#TCP Server w message pack
import logging
import time
import sys
import os
import numpy as np
import socket
import json
from datetime import datetime
import subprocess
import signal
from contextlib import contextmanager
import datetime

log = logging.getLogger('TCP SERVER')
HEADER_SIZE = 32

class RandomTCPError(Exception):
   """Raised when A random tcp error occured"""
   pass


@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.alarm(time)
    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)

def raise_timeout(signum, frame):
    raise TimeoutError

class TCPServer():
    """
        This is a simple TCP server streaming a file like object out from Audio Recorder and to a client.
        The protocol is request reply driven. 
        The Client must make a request within timeout or the recording will abort.
        The TCP Server thread is notified by new_data event.  
         
    """

    def __init__(self, host_ip, port, e_new_data, e_abort):
        log.info("Threaded TCP SERVER initializing")
        super(TCPServer,self).__init__()
        self.ip = host_ip
        self.port = port
        log.info("Server ip = " + str(self.ip) + " Application Port = " + str(self.port))
        self.has_client = False
        self.server = None self.__setup_server()
        self.connection = self.__setup_connection()
        self.file_like_obj = self.server.makefile("w")
        self.new_data = e_new_data
        self.abort = e_abort
        
        log.info("Class initialized")
        log.info("Entering Data Transfer Loop")
        self.startTime = 0

    def __is_client_connected(self):
        return self.has_client

    def __is_new_data(self):
        return self.new_data.isSet()
    
    
    @staticmethod
    def encode_reply(reply):
        try:
            res = reply.encode("UTF-8")
            return res, len(res)
        except TypeError as err:
            log.info("Error encoding UTF: {}".format(err))
        #    raise RedisPubSubError('Error encoding msgpack: {}'.format(err))

    @staticmethod
    def pad_payload(request):
        return request.ljust(HEADER_SIZE, '-')

    @staticmethod
    def client_request(connection):
        try:
            buf = connection.recv(HEADER_SIZE)
            log.debug("Client Message Received, decoding reply")
            resp = buf.decode('UTF-8')
            log.debug("Response : {}".format(resp))
            return resp

        except TypeError as err:
            log.info("Error decoding client request: {}".format(err))

    def __setup_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log.info("Socket created.")
        try:
            s.bind((self.ip, self.port))
            #s.settimeout(10)
        except socket.error as msg:
            print(msg)
        log.info("Socket bind complete")
        return s
    
    def __setup_connection(self):
        try:
            self.server.listen(1)  # Allows one connection at a time.
            conn, address = self.server.accept()
            log.info("Connected to: " + address[0] + ":" + str(address[1]))
            conn.settimeout(5.0)
            return conn
        except:
            log.warning("Error in Setup Connection : ")
            self.reconnect_server()


    def set_time(self, epoch):
        '''
        Sets the Server internal time.
         @input - unix epoch time.
        '''
        log.info('Setting time to epoch %s', str(epoch))
        if epoch != 0:
            subprocess.run('sudo /bin/date -s @' + str(epoch), shell=True, stdout=subprocess.DEVNULL)

    
    def REPEAT(self, dataMessage):
        try:
            reply = dataMessage
            reply = self.pad_payload(reply)
            msg = reply.encode('UTF-8')
            self.connection.sendall(msg)
            return True
        except:
            return False

    def GET_DATA(self):
        try:
            msg, meta = self.encode_result(self.payload.result_dict)
            # Header string is message lengths in a : separated list
            tmp_header = ""
            separator = ':'
            for info in meta:
                tmp_header += "{}{}".format(info, separator)
            header = self.pad_payload(tmp_header)
            log.info("Header : {}".format(header))
            self.connection.sendall(header.encode('UTF-8'))
            payload_len = 0
            for part in msg:
                msglen = len(part)
                log.debug("Sending Sub Message of len = {}".format(msglen))
                self.connection.sendall(part)
                payload_len += msglen
                time.sleep(0.01)
            log.debug("Payload Sent, Total data len = {}".format(payload_len))
            return True
        except:
            return False

    def GET_DATETIME(self):
        now = datetime.datetime.now()
        d1 = now.strftime("%Y-%m-%d %H:%M:%S")
        self.connection.sendall(d1.encode('UTF-8'))

    def SET_DATETIME(self,epoch):
        pass

    @staticmethod
    #This method removes padding used to make req/reply static of length
    def __strip_header_padding(msg):
        return ''.join(c for c in msg if c not in '-')

    def server_loop(self):
        # A loop that sends/receive data until told not to.
        socket_fault = False
        while True:
            try:
                
                # Receive the data
                self.lCounter += 1
                log.info("Waiting for client request # %i" %self.lCounter)
                data = self.client_request(self.connection)
                self.has_client = True
                data = self.strip_excess(data)
                log.debug("Request received : {}".format(data))
                dataMessage = data.split(':', 1)
                command = dataMessage[0]
                log.info("Command : {}".format(command))

                if command == 'GET_CONFIGA':
                    self.GET_CONFIG_A()
                    log.info("sent reply with config")

                elif command == 'GET_CONFIGB':
                    self.GET_CONFIG_B()
                    log.info("sent reply with config")

                elif command == 'SET_CONFIGA':
                    log.info("Setting config A, waiting for {} Bytes".format(dataMessage[1]))
                    self.SET_CONFIG_A(dataMessage[1])

                elif command == 'SET_CONFIGB':
                    log.info("Setting config B, waiting for {} Bytes".format(dataMessage[1]))
                    self.SET_CONFIG_B(dataMessage[1])

                elif command == 'GET_DATA':
                    if self.GETDATA():
                        log.debug("sent reply with data")
                    else:
                        log.warning("Failed to send reply with data")
                        raise ValueError('A very specific bad thing happened')

                elif command == 'REPEAT':
                    if self.REPEAT(command):
                        log.info("send reply REPEAT")
                    else:
                        raise ValueError('A very specific bad thing happened')

                elif command == 'SET_TIME':
                    try:
                        epoch = int(dataMessage[1])
                        self.set_time(epoch)
                        ts = datetime.datetime.now().timestamp()
                        message = "SET_TIME:{}".format(int(ts))
                        log.info("SET_TIME RESPONSE - ".format(message))
                    except:
                        message = "FAILED TO SET TIME"
                        log.warning("SET_TIME RESPONSE - ".format(message))
                    msg = self.pad_payload(message)
                    self.connection.sendall(msg.encode('UTF-8'))

                elif command == 'EXIT':
                    log.info("Our client has left us :(")
                    connected = False
                    break

                elif command == 'KILL':
                    log.info("Our system is shutting down.")
                    self.connection.close()
                    self.server.close()
                    exit()
                else:
                    reply = 'Unknown command'.encode('utf-8')
                    log.info("{}".format(reply))
                    try:
                        self.connection.sendall(reply)
                        log.info("Still Connected")
                    except:
                        log.info("Failed connection..")
                        del data
                        del dataMessage
                        del command
                        raise ValueError('A very specific bad thing happened')

                log.info("Data has been sent")

            except (socket.error,ValueError, socket.timeout ) as e:
                log.info("Lost Client connection... Trying reconnect")
                self.socket_error = True
                self.has_client = False
                self.reconnect_server()
        self.connection.close()


    def reconnect_server(self):
        try:
            self.connection.close()
            self.server.close()
            time.sleep(0.5)
            self.server = self.setupServer()
            self.server.settimeout(5)
            self.connection = self.setupConnection()
            self.server.setblocking(False)
            self.connection.settimeout(5)
            self.dataTransfer()
        except:
            self.has_client = False
            self.socket_error = True