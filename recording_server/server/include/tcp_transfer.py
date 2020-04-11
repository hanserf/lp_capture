"""
    Based on
    https://stackoverflow.com/questions/48812854/python3-sending-files-via-socket
"""
import logging
import io
import socket
import wave
import time
from threading import Event,Thread,BoundedSemaphore
from queue import Queue

log = logging.getLogger("TCP-SERVER")
HEADER_SIZE = 32

class NoACK(Exception):
    """Raised when A random modbus error occured"""
    pass

class BufferTransfer():
    """
        Use and throw interface for transferring a json from control out to clients.
        The server will initialize with the file to send
        
    """
    mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    mysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    @staticmethod
    def __pad_header(header):
        # This methods pads and encodes header
        header.ljust(HEADER_SIZE, '-')
        return header.encode("UTF-8")

    @staticmethod
    def __strip_header(header):
        # This method removes padding used to make req/reply static
        req_header = header.decode('UTF-8')
        unpadded = ''.join(c for c in req_header if c not in '-')
        return unpadded.split(':', 1)
    
    
    def __init__(self,uid,file_size_tuple, ip_port_tuple, n_clients=1,status_callback=None):
        log.debug()
        self.uid = uid
        self.status_callback = status_callback
        self.mysocket.bind(ip_port_tuple)
        self.mysocket.listen(n_clients)
        conn, addr = self.mysocket.accept()
        self.stream_sem = BoundedSemaphore(value=n_clients)
        for i in range(1,n_clients):
            thread_identifier = (uid,i)
            thread_name = "BUFFER-TRANSFER:{},ThreadID:{}".format(uid,i)
            send_thread = Thread(name=thread_name,target=self.__send_file, args=(thread_identifier,file_size_tuple, conn, addr, ))
            send_thread.start()

    def __get_client_request(self,conn):
        active_client = False
        raw_header = conn.recv(HEADER_SIZE)
        header = self.__strip_header(raw_header)
        if header[0] == "GET_STREAM":
            active_client = True
        return active_client

    def __send_file(self, thread_identifier, file_size_tuple, conn, addr):
        file_like, size = file_size_tuple
        self.mysocket.setblocking(False)
        self.mysocket.settimeout(1)
        if self.__get_client_request(conn):
            with open(file_like, 'rb') as stream_frame:
                request = "{}:{}".format(thread_identifier[0],size)
                header = self.__pad_header(request)
                conn.send_all(header)
                data = stream_frame.read(int(size))
                conn.sendall(data)
                ack = conn.recv(HEADER_SIZE)   
                if ack == "SUCCESS:{}".format(request):
                    self.stream_sem.release()
                    log.debug(' THREAD ID : {}, TRANSFER-SUCCESSFULL,{}'.format(thread_identifier[1],request))
                    
        else:
            self.status_callback("NO_CLIENT:{}".format(thread_identifier[1]))
            self.stream_sem.release()
            
    def acknowledge_send(self):
        sucess = False
        try:
            if not self.stream_sem.acquire(timeout=2):
                log.info("EXCEPTION, NO ACK - SEMAPHORE TIMEOUT")
                raise NoACK
            else:
                sucess=True
                self.status_callback("SUCESS")
        except NoACK:
            self.status_callback("FAILED:{}".format(self.uid))
            
        finally:
            self.mysocket.shutdown(socket.SHUT_RDWR)
            self.mysocket.close()
            if sucess:
                return True
            else:
                return False