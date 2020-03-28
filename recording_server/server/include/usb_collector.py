import time
import sys
import numpy as np
import sys
import os
import io
from threading import Thread, BoundedSemaphore, Event

from queue import Queue
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)
import logging

"""
This class interacts with hardware module and is based on some tutorial.
The USB Collector interacts with a USB sound device and captures samplestream into a buffer
It uses threading to capture input stream.
Device and buffer Semaphore for source exclusivety and synchronization
Records data to ram using io.ByteIO()
 
"""

log = logging.getLogger('LP-Server')

class SoundDeviceError(Exception):
   """Raised when A random Sounddevice error occured"""
   pass

class SoundDeviceStop(Exception):
   """Raised when A random Sounddevice error occured"""
   pass


class USBCollector(Thread):
    def __init__(self, buffer_window_s,args, parser, rec_folder):
        super(USBCollector, self).__init__()
        self.args = args
        self.parser = parser
        self.device_sem = BoundedSemaphore()
        self.done_sem = BoundedSemaphore()    
        self.buffer = Queue()
        self.__init_sounddevice(buffer_window_s)
        self.sound_file = None
        self.capture_buffer_timeout = buffer_window_s
        self.aborted = Event()

    def __init_sounddevice(self,buffer_window_s):
        """
            Take the sounddevice
            Parse device info into control argments
        """
        try :
            self.device_sem.acquire()
            device_info = sd.query_devices(self.args.device, 'input')
            # soundfile expects an int, sounddevice provides a float:
            self.args.name = device_info['name']
            self.args.samplerate = int(device_info['default_samplerate'])
            self.args.buffersize = int(self.args.samplerate*float(buffer_window_s))
            self.args.channels = device_info['max_input_channels']
            if self.args.file is None:
                buffer_file =  io.ByteIO()
                self.args.file = buffer_file
        except:
            raise SoundDeviceError
        finally:
            self.device_sem.release()


    def __enable_recording(self):
        try:
            
            self.device_sem.acquire()
            log.info("->INPUT-DEVICE-AQUIRED")
            # Make sure the file is opened before recording anything:
            with sf.SoundFile(self.args.file, mode='x', samplerate=self.args.samplerate,channels=self.args.channels, subtype=self.args.subtype) as self.sound_file:
                cThread = Thread(name="CAPTURE", target=self.__start_capture)
                cThread.start()
                cThread.join()

        except KeyboardInterrupt:
            log.info("->ABORT-EXIT")
            print('\nRecording finished')
            cThread.join()
            self.parser.exit(0)
                  
        except Exception as e:
            self.parser.exit(type(e).__name__ + ': ' + str(e))
        
        finally:
            log.info("->CAPTURE-COMPLETE")
            print('\nRecording finished')
            self.device_sem.release()
            

    def __start_capture(self) -> None:
        print("Entering Recording loop")
        log.info("-->CAPTURE-START")
        try: 
            with sd.InputStream(samplerate=self.args.samplerate, device=self.args.device, channels=self.args.channels, callback=self.__buffer_callback):
                
                while True:
                    self.done_sem.acquire(timeout=self.capture_buffer_timeout)
                    if not self.__is_aborted():
                        log.debug("---->CAPTURE BUFFER TO FILE")
                        raw_data = self.buffer.get()
                        self.sound_file.write(raw_data)
                        self.done_sem.release()
                    else:
                        self.done_sem.release()
                        break
    
        except SoundDeviceStop:
            self.aborted.set()
            

    def __buffer_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.buffer.put(indata.copy())

    def __is_aborted(self):
        return self.aborted.isSet()

   
def test():
    # Create Logger / Log Handler
    log_level = logging.DEBUG
    log = logging.getLogger()
    log.setLevel(log_level)
    fh = logging.FileHandler('lp_server_logfile.txt')
    fh.setLevel(log_level)
    log.addHandler(fh)
    log_format = ('%(asctime)-15s %(threadName)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
    log_formatter = logging.Formatter(log_format)
    fh.setFormatter(log_formatter)

if __name__ == "__main__":
    test()