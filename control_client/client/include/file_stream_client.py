import io
import socket
import wave
import time
from threading import Event, Thread, BoundedSemaphore
from queue import Queue


class FileStreamClient():
    def __init__(self, file_buffer, e_abort, port=3739):
        self.socket = socket.socket()
        ip_addr = self.__get_system_ip(local_only=False)
        conn_union = (ip_addr, port)
        self.socket.connect(conn_union)
        self.abort = e_abort
        self.new_data = Event()
        self.file_buffer = file_buffer
        self.link_semaphore = BoundedSemaphore(value=1)

    def get_file_from_buffer():
        try:

    def __get_system_ip(self, local_only=True):
        if local_only:
            # Setting IP to serve address from network
            my_ip = (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [
                [(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in
                 [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0]
        else:
            # Setting ip to serve any connection from any net.
            my_ip = "0.0.0.0"
        return my_ip

    def __file_streaming_loop(self):

        enable = True
        tmp_file = io.BytesIO()
        cntr = 0
        while enable:
            if self.__is_new_data():
                cntr += 1
                dummy.write(self.recorder.return_recording_as_file())
                dummy.seek(0)
                dummy.seek(0, os.SEEK_END)
                size = dummy.tell()
                print("Data Append #{}to file\n File Size = {}".format(cntr, size))
                self.new_data.clear()
            else:
                if self.abort.is_set():
                    break
                else:
                    time.sleep(0.5)

        with open(tmp_file, "rb") as file_stream:
            data = filetosend.read(1024)
            while enable:
                if self.__is_new_data():
                    json_file, size =
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
                    # Done :)