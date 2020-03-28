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
Thread callback collects samples from input device into a Queue buffer structure.
Acquiring the semaphore will write the content of the buffer queue into the ram file. 
Ram file is created using io.ByteIO()

 
"""

log = logging.getLogger('LP-Server')

class SoundDeviceError(Exception):
   """Raised when A random Sounddevice error occured"""
   pass

class SoundDeviceStop(Exception):
   """Raised when A random Sounddevice error occured"""
   pass


class AudioRecorder(Thread):
    def __init__(self, buffer_window_s,args, parser, uptime_callback=None):
        super(AudioRecorder, self).__init__()
        self.args = args
        self.parser = parser
        self.device_sem = BoundedSemaphore()
        self.done_sem = BoundedSemaphore()    
        self.buffer = Queue()
        self.__init_sounddevice(buffer_window_s)
        self.sound_file = None
        self.capture_buffer_timeout = buffer_window_s
        self.aborted = Event()
        self.uptime_callback = uptime_callback
        self.start_time

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
            self.uptime_callback(0)
        except:
            raise SoundDeviceError
        finally:
            self.device_sem.release()
    
    def __clear_abort(self):
        self.aborted.clear()

    def __is_aborted(self):
        return self.aborted.isSet()
         
    def stop_recording(self):
        self.aborted.set()           


    def enable_recording(self, timeout, n_attempts):
        cntr = 0
        while cntr <n_attempts:
            try:
                if not self.__enable_recording(timeout):
                    raise SoundDeviceError
                return True
            except SoundDeviceError:
                print("Struggling to connect with recording device. Please check connections or input settings")
                cntr+=1    
            except KeyboardInterrupt:
                break
        return False

    """
        __enable recording controls the capture thread.
    """
    def __enable_recording(self,timeout):
        try:
            if not self.device_sem.acquire(timeout=timeout):
                raise SoundDeviceError
            log.info("->INPUT-DEVICE-AQUIRED")
            # Make sure the file is opened before recording anything:
            with sf.SoundFile(self.args.file, mode='x', samplerate=self.args.samplerate,channels=self.args.channels, subtype=self.args.subtype) as self.sound_file:
                cThread = Thread(name="CAPTURE", target=self.__start_capture)
                cThread.start()
                cThread.join()

        except (KeyboardInterrupt,SoundDeviceStop):
            self.stop_recording()
            log.info("->ABORT-EXIT")
            print('\nRecording finished')
            cThread.join()
        
        except SoundDeviceError:
            raise
        finally:
            self.device_sem.release()
            if self.__is_aborted():
                log.info("->CAPTURE-ABORTED")
                print('\nRecording Aborted')
                return False
                
            log.info("->CAPTURE-COMPLETE")
            print('\nRecording finished')
            return True

    def __start_capture(self) -> None:
        print("Entering Recording loop")
        log.info("-->CAPTURE-START")
        self.__clear_abort()    
        try: 
            self.start_time = time.time()
            uptime = 0
            with sd.InputStream(samplerate=self.args.samplerate, device=self.args.device, channels=self.args.channels, callback=self.__buffer_callback):
                while True:
                    self.done_sem.acquire(timeout=self.capture_buffer_timeout)
                    if not self.__is_aborted():
                        uptime = time.time()-self.start_time 
                        self.uptime_callback(uptime)
                        log.debug("---->CAPTURE BUFFER TO FILE, UPTIME: {}".format(uptime))
                        raw_data = self.buffer.get()
                        self.sound_file.write(raw_data)
                        self.done_sem.release()
                    else:
                        self.done_sem.release()
                        break
                self.uptime_callback(0)
    
        except SoundDeviceStop:
            self.aborted.set()
            
    def __buffer_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.buffer.put(indata.copy())
    
    def read_file_raw(self,n_retries,timeout):
        cntr = 0
        while cntr < n_retries:
            try:
                if not self.done_sem.acquire(timeout=timeout):
                    raise SoundDeviceError
                output = io.BytesIO()
                output.write(self.sound_file.read())
                self.done_sem.release()
                return output.getvalue()
            except SoundDeviceError:
                cntr += 1
            except KeyboardInterrupt:
                break
        return None
   
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