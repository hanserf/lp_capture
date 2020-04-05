import time
import sys
import sys
import os
import io
from datetime import datetime
from threading import Thread, BoundedSemaphore, Event
import wave 
from queue import Queue
import sounddevice as sd
import soundfile as sf
#import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)
import logging

"""
This class interacts with hardware module and is based on some tutorial.
The USB Collector interacts with a USB sound device and captures samplestream into a buffer
It uses threading to capture input stream.
Device and buffer Semaphore for source exclusivety and synchronization
Thread callback collects samples from input device into a Queue buffer structure.
Acquiring the semaphore will write the content of the buffer queue into the ram file. 
Ram file is created using io.ByteIO()

 
"""

log = logging.getLogger('AudioRecorder')

class SoundDeviceError(Exception):
   """Raised when A random Sounddevice error occured"""
   pass

class SoundDeviceStop(Exception):
   """Raised when A random Sounddevice error occured"""
   pass


class AudioRecorder(Thread):
    def __init__(self, args, parser,e_new_data,e_abort, uptime_callback=None):
        super(AudioRecorder, self).__init__()
        self.args = args
        self.parser = parser
        self.recording_sem = BoundedSemaphore(value=1)    
        self.buffer = Queue()
        self.sound_file = None
        self.capture_buffer_timeout = 0
        self.aborted = e_abort
        self.new_data = e_new_data
        self.uptime_callback = uptime_callback
        self.start_time = 0
        self.sucess = False


    def init_sounddevice(self):
        """
            Take the sounddevice
            Parse device info into control argments
        """
        try :
            self.capture_buffer_timeout = self.args.buffer_width_s[0]
            device_info = sd.query_devices(self.args.device, 'input')
            print("Device Info :")
            for key in device_info:
                print("{}:{}".format(key,device_info[key]))
            self.args.name = device_info['name']
            self.args.samplerate = int(device_info['default_samplerate'])
            self.args.buffersize = int(self.args.samplerate*float(self.capture_buffer_timeout))
            if self.args.file is None:
                self.sound_file = io.BytesIO()
            log.debug("Device Initialized")
                    
        except:
            log.warning("Device failed to initialize")
            raise SoundDeviceError
    
    def __clear_abort(self):
        self.sucess = True
        self.aborted.clear()

    def __is_aborted(self):
        return self.aborted.isSet()
         
    def stop_recording(self):
        log.info("Recording stopped : {}".format(datetime.now()))
        self.aborted.set()           

    """
        enable recording controls the capture thread.
    """
    def enable_recording(self):
        try:
            #Take Recording Semaphore
            self.uptime_callback(0)       
            self.recording_sem.acquire()
            self.__clear_abort()
            log.info("->INPUT-DEVICE-AQUIRED")
            # Make sure the file is opened before recording anything:
            cThread = Thread(name="CAPTURE", target=self.__start_capture)
            cThread.start()
            time.sleep(0.5)
            #Release semaphore so that the thread may start capturing recorded buffer to file
            self.recording_sem.release()
            
        except Exception as e:
            print(e)
            self.stop_recording()
            log.info("->ABORT-EXIT")
            print('\nRecording finished')
            cThread.join()
        

    def __start_capture(self) -> None:
        print("Entering Recording loop")
        log.info("-->CAPTURE-START")
        self.__clear_abort()    
        with sd.InputStream(samplerate=self.args.samplerate, device=self.args.device, channels=self.args.channels, callback=self.__buffer_callback):
            self.start_time = time.time()
            uptime = 0
            while True:
                uptime = time.time() - self.start_time 
                self.uptime_callback(uptime)
                if not self.__is_aborted():
                    raw_data = self.buffer.get()
                    self.sound_file.write(raw_data)
                    self.new_data.set()
                    #self.recording_sem.release()
                    
                else:
                    break
                
                
    def __buffer_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.buffer.put(indata)
    
    def read_file_raw(self):
        ret_val =self.sound_file.getvalue()
        log.debug("READ:{}".format(len(ret_val))) 
        return ret_val
        
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