import logging
import json
import io
import os
from threading import Event
from queue import Queue
import argparse
import sounddevice as sd

from server.include.worker import Worker

log = logging.getLogger("CONTROL")

class Control():
    
    def __init__(self ):
        self.abort = Event()
        self.new_payload = Event()
        self.streaming_dict = { "start_time":0,
                                "frame_count":0,
                                "compression":False,
                                "buffer_size":0,
                                "stream_buffer":0 }
        
        self.worker = Worker(e_abort=self.abort, json_dictionary_callback=self.file_object_callback)
        self.buffer = Queue()
        
    
    def __is_new_payload(self):
        return self.new_payload.isSet()

    def file_object_callback(self, start_time, current_framecount,compression,file_size, file_like):
        result = self.streaming_dict
        result["start_time"] = start_time
        result["frame_count"] = current_framecount
        result["compression"] = compression
        result["size"] = file_size
        result["stream_buffer"] = file_like
        (json_like,packet_size) = self.__dict_to_json_file_like(result)
        payload_tuple = (json_like,packet_size)
        self.buffer.put(payload_tuple)
        self.new_payload.set()
        
    def __dict_to_json_file_like(self,dict):
        file = io.BytesIO()
        json.dump(dict, file)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        log.debug("Result dict converted to json of size:{}".format(size))
        file_like = file.getvalue()
        return file_like, size
    
    def do_init(self,inp):
    
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(
            '-buf', '--buffer_width_s',type=float, nargs=1,
            help='Buffer width in seconds')
        parser.add_argument(
            '-l', '--list-devices', action='store_true',
            help='show list of audio devices and exit')
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[parser])
        parser.add_argument(
            'file', nargs='?',default=None, metavar='FILENAME',
            help='Capture file, Defaults to ram')

        parser.add_argument(
            '-d', '--device', type=self.__int_or_str,
            help='input device (numeric ID or substring)')
        parser.add_argument(
            '-r', '--samplerate', type=int, help='sampling rate')
        parser.add_argument(
            '-c', '--channels', type=int, default=2, help='number of input channels')
        parser.add_argument(
            '-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
        parser.add_argument(
            '-bt', '--timeout', type=int, default=5, help='Buffer read timeout')
        parser.add_argument(
            '-nr', '--num_retries', type=int, default=3, help='Number of attempts the application will make to succeed')

        args = parser.parse_known_args()
        args = parser.parse_args(inp.split())
        if args.list_devices:
            print(sd.query_devices())
        """
            Setting this argument will arm worker.
            A recording command may be issued after this.
            Starting and stopping worker will require re-arming interface.
        """
        if args.buffer_width_s:
            self.worker.init_worker(args,parser)