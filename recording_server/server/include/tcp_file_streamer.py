import io
import socket
import wave
import time
from threading import Event,Thread
from queue import Queue
class FileStreamClient():
    def __init__(self,ip_addr="localhost", port=3739):
        self.socket = socket.socket()
        conn_union = (ip_addr, port)
        self.socket.connect(conn_union)
        self.abort = Event()
        self.new_data = Event()

    def __is_new_data(self):
        return self.new_data.is_set()

    def readback_loop(self):

    def __file_streaming_loop(self):
        enable = True
        dummy = io.BytesIO()
        cntr = 0
        while enable:
            if self.__is_new_data():
                cntr += 1
                dummy.write(self.recorder.return_recording_as_file())
                dummy.seek(0)
                dummy.seek(0, os.SEEK_END)
                size = dummy.tell()
                print("Data Append #{}to file\n File Size = {}".format(cntr,size))
                self.new_data.clear()
            else:
                if self.abort.is_set():
                    break
                else:
                    time.sleep(0.5)


        filetosend = open("img.png", "rb")
        data = filetosend.read(1024)
        while data:
            print("Sending...")
            s.send(data)
            data = filetosend.read(1024)
        filetosend.close()
        s.send(b"DONE")
        print("Done Sending.")
        print(s.recv(1024))
        s.shutdown(2)
        s.close()
        #Done :)