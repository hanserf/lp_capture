"""
From
https://stackoverflow.com/questions/48812854/python3-sending-files-via-socket
Just
"""

import socket, sys
import io
from threading import Thread, BoundedSemaphore
import os
import logging
from time import sleep

HEADER_SIZE = 32
log = logging.getLogger("STREAM-RECEIVE")
streaming_dict = {"start_time": 0,
                  "frame_count": 0,
                  "compression": False,
                  "buffer_size": 0,
                  "stream_buffer": 0}


class BufferReceive():
    """
        Result Callback is Uid, Size and File
        Aquiring
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

    def __init__(self,ip_port_tuple,status_callback=None,result_callback=None):
        self.mysocket.connect(ip_port_tuple)
        self.mysocket.setblocking(False)
        self.mysocket.settimeout(1)
        self.receive_sem = BoundedSemaphore(value=1)
        self.result_callback = result_callback

    def __send_header(self):
        request = "GET_STREAM"
        header = self.__pad_header(request)
        self.mysocket.sendall(header)

    def __send_ack(self,uid,size):
        done_ack = "SUCCESS:{}:{}".format(uid, size)
        ack_header = self.__pad_header(done_ack)
        self.mysocket.sendall(ack_header)

    def __receive_stream(self):
        self.receive_sem.acquire()
        stream_frame = io.BytesIO()
        success = False
        size = None
        uid = None
        file_like = None
        self.__send_header()
        try:
            client_ack = self.mysocket.recv(HEADER_SIZE)
            reply = self.__strip_header(client_ack)
            uid = reply[0]
            size = reply[1]
            data = self.mysocket.recv(int(size))
            stream_frame.write(data)
            success = True

        except socket.timeout as e:
            log.warning("Socket Timeout : {}".format(e))

        finally:
            if success:
                stream_frame.seek(0, os.SEEK_END)
                rx_size = stream_frame.tell()
                stream_frame.seek(0)
                if rx_size == int(size):
                    self.__send_ack(uid,rx_size)
                    file_like = stream_frame.getvalue()
            self.result_callback(uid,size,file_like)
            self.receive_sem.release()
