from threading import Event
from queue import Queue

from server.include.worker import Worker

class Control():
    
    def __init__(self ):
        self.abort = Event()
        self.new_result = Event()
        self.new_request = Event()
        self.streaming_dict = { "start_time":0,
                                "frame_count":0,
                                "compression":False,
                                "buffer_size":0,
                                "stream_buffer":0 }
        self.worker = Worker(e_abort=self.abort,e_new_request=self.new_request,json_dictionary_callback=self.file_object_callback)
        self.buffer = Queue()
        
    
    def __is_new_result(self):
        return self.new_result.isSet()

    def file_object_callback(self, start_time, current_framecount,compression,file_size, file_like):
        result = self.streaming_dict
        result["start_time"] = start_time
        result["frame_count"] = current_framecount
        result["compression"] = compression
        result["size"] = file_size
        result["stream_buffer"] = file_like
        self.new_result.set()