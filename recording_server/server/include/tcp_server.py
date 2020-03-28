#TCP Server w message pack
import logging
import time
import sys
import os
import numpy as np
import msgpack
import socket
import json
from datetime import datetime
import subprocess
from rsep_tcp.include.config_parser import ConfigParser
import signal
from contextlib import contextmanager
import datetime

log = logging.getLogger('TCP SERVER')
HEADER_SIZE = 64

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

class ResultDict:
    def __init__(self, data_size):
        self.result_dict = {"index":0,"epoch":0, "t_zero":1.0, "t_menisk":1.0 ,"t_ref":1.0,"v_ref":1.0,"d_menisk":1.0,"t_start":0,"raw_data":[] }
        self.new_result = False
        self.result_transmitted = False

    def update_result(self, index, data, unix_time, t_zero, t_menisk, t_ref, v_ref, d_minisk,t_start,):
        self.result_dict["index"] = index
        self.result_dict["epoch"] = unix_time
        self.result_dict["t_zero"] = t_zero
        self.result_dict["t_menisk"] = t_menisk
        self.result_dict["t_ref"] = t_ref
        self.result_dict["v_ref"] = v_ref
        self.result_dict["d_menisk"] = d_minisk
        self.result_dict["t_start"] = t_start
        self.result_dict["raw_data"] = data
        self.new_result = True
        self.result_transmitted = False

    def is_new_result(self):
        return self.new_result

    def unset_new_result(self):
        self.new_result = False

    def is_result_transmitted(self):
        return self.result_transmitted

    def set_result_transmitted(self):
        self.result_transmitted = True



class TCPServer():

    def __init__(self, host_ip, port, data_size,configA,configB, config_dir):
        log.info("Hello world, Threaded TCP initializing")
        super(TCPServer,self).__init__()
        self.ip = host_ip
        self.port = port
        log.info("Server ip = " + str(self.ip) + " Application Port = " + str(self.port))
        self.lCounter = 0
        self.has_client = False
        self.socket_error = False
        self.config_dir = config_dir
        try:
            self.server = self.setupServer()
        except:
            log.critical("Could not create server. Exiting")
            exit(1)
        self.connection = self.setupConnection()
        log.info("Class initialized")
        self.payload = ResultDict(data_size)
        self.myConfigA = configA
        self.myConfigB = configB
        log.info("Entering Data Transfer Loop")
        self.startTime = 0

    def is_client_connected(self):
        return self.has_client

    @staticmethod
    def encode_reply(reply):
        try:
            res = msgpack.packb(reply)
            return res, len(res)
        except TypeError as err:
            log.info("Error encoding msgpack: {}".format(err))
        #    raise RedisPubSubError('Error encoding msgpack: {}'.format(err))

    def encode_result(self,result_dict):
        msg = []
        header = []
        cntr = 0
        for entry in result_dict:
            try:
                chunk, size_chunk = self.encode_reply(entry)
                msg.append(chunk)
                header.append(size_chunk)
                log.debug("INDEX: {} KEY: {} Appending: {} ".format(cntr,entry,size_chunk))
                cntr += 1
                chunk, size_chunk = self.encode_reply(result_dict[entry])
                msg.append(chunk)
                header.append(size_chunk)
                cntr += 1
                log.debug("INDEX: {} KEY: {} Appending: {} ".format(cntr, entry, size_chunk))
                cntr += 1
            except TypeError as err:
                log.info("Error encoding msgpack: {}".format(err))

        return msg, header

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

    def setupServer(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log.info("Socket created.")
        try:
            s.bind((self.ip, self.port))
            #s.settimeout(10)
        except socket.error as msg:
            print(msg)
        log.info("Socket bind complete")
        return s

    def set_time(self, epoch):
        '''
        Sets the Datalogger internal time.
         @input - unix epoch time.
        '''
        log.info('Setting time to epoch %s', str(epoch))
        if epoch != 0:
            subprocess.run('sudo /bin/date -s @' + str(epoch), shell=True, stdout=subprocess.DEVNULL)

    def setupConnection(self):
        try:
            self.server.listen(1)  # Allows one connection at a time.
            conn, address = self.server.accept()
            log.info("Connected to: " + address[0] + ":" + str(address[1]))
            conn.settimeout(5.0)
            return conn
        except:
            log.warning("Error in Setup Connection : ")
            self.reconnect_server()



    def GET_CONFIG_A(self):
        reply, reply_len = self.myConfigA.encode_config_utf8()
        if reply is not None:
            log.info("Sending config A {}:{}".format(reply_len,reply))
            header = self.pad_payload(str(reply_len))
            self.connection.sendall(header.encode('UTF-8'))
            self.connection.sendall(reply)
        else:
            raise ValueError('Bad stuff Sending config B')

    def GET_CONFIG_B(self):
        reply, reply_len = self.myConfigB.encode_config_utf8()
        if reply is not None:
            log.info("Sending config B {}:{}".format(reply_len, reply))
            header = self.pad_payload(str(reply_len))
            self.connection.sendall(header.encode('UTF-8'))
            self.connection.sendall(reply)
        else:
            raise ValueError('Bad stuff Sending config B')


    def SET_CONFIG_B(self,expected_config_len):
        config_raw = self.connection.recv(int(expected_config_len))
        log.info("Received ConfigB raw:{}".format(config_raw))
        config_string = config_raw.decode('UTF-8')
        log.info("Received ConfigB:{}".format(config_string))
        config_list = config_string.split(',')
        log.info("Config List [" + ' , '.join(config_list) + ']')
        for config in config_list:
            if config == '':
                pass
            else:
                key,value = config.split(':')
                log.info("Received Config KEY = {}, Value = {}".format(key,value))
                self.myConfigB.set_config(key,value)
        config_path = "{}/configB.json".format(self.config_dir)
        log.info("Config path: {}".format(config_path))
        self.myConfigB.save_config(config_path)
        self.GET_CONFIG_B()

    def SET_CONFIG_A(self,expected_config_len):
        config_raw = self.connection.recv(int(expected_config_len))
        log.info("Received ConfigB raw:{}".format(config_raw))
        config_string = config_raw.decode('UTF-8')
        log.info("Received ConfigB:{}".format(config_string))
        config_list = config_string.split(',')
        for config in config_list:
            if config =='':
                pass
            else:
                key,value = config.split(':')
                log.info("Received Config KEY = {}, Value = {}".format(key,value))
                self.myConfigA.set_config(key,value)

        config_path = "{}/configB.json".format(self.config_dir)
        log.info("Config path: {}".format(config_path))
        self.myConfigA.save_config(config_path)
        self.GET_CONFIG_A()


    def REPEAT(self, dataMessage):
        try:
            reply = dataMessage
            reply = self.pad_payload(reply)
            msg = reply.encode('UTF-8')
            self.connection.sendall(msg)
            return True
        except:
            return False

    def GETDATA(self):
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
        now = datetime.now()
        d1 = now.strftime("%Y-%m-%d %H:%M:%S")
        self.connection.sendall(d1.encode('UTF-8'))

    def SET_DATETIME(self,epoch):
        pass

    @staticmethod
    #This method removes padding used to make req/reply static of length
    def strip_excess(msg):
        return ''.join(c for c in msg if c not in '-')

    def dataTransfer(self):
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