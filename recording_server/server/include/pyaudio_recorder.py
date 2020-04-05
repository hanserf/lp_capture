import pyaudio
import wave
from threading import Event,Thread,BoundedSemaphore
from queue import Queue
import sounddevice as sd
import logging
import time
import io
from datetime import datetime

log = logging.getLogger("PYAUDIO-RECORDER")

class pyAudioRecorder():
    def __init__(self, args, parser, e_new_data,e_abort, framecount_callback=None):
        super(pyAudioRecorder, self).__init__()
        self.args = args
        self.parser = parser
        self.recording_sem = BoundedSemaphore(value=1)    
        self.buffer = Queue() 
        self.sound_file = io.BytesIO()
        self.rec_proc = pyaudio.PyAudio()
        self.capture_buffer_width = 0
        self.aborted = e_abort
        self.new_data = e_new_data
        self.framecount_callback = framecount_callback
        self.start_time = 0
        self.recThread = None
        
    
    def __is_aborted(self):
        return self.aborted.isSet()
    
    def init_sounddevice(self):
        """
            Take the sounddevice
            Parse device info into control argments
        """
        try :
            self.capture_buffer_width = self.args.buffer_width_s[0]
            device_info = sd.query_devices(self.args.device, 'input')
            print("Device Info :")
            for key in device_info:
                print("{} : {}".format(key,device_info[key]))
            self.args.name = device_info['name']
            self.args.samplerate = int(device_info['default_samplerate'])
            self.args.buffersize = int(self.args.samplerate*float(self.capture_buffer_width))
            self.args.sample_format = pyaudio.paInt16  # 16 bits per sample
            self.args.chunk = 1024  # Record in chunks of 1024 samples
            if self.args.file is not None:
                self.sound_file = self.args.file
                       
            log.debug("Device Initialized") 
            
        except:
            log.warning("Device failed to initialize")
            raise
        
    def __start_capture(self) -> None:
        print("Entering Recording loop")
        log.info("-->CAPTURE-START")
        log.info("Opening Stream : {}".format(datetime.now()))
        stream = self.rec_proc.open(format=self.args.sample_format,
                        channels=self.args.channels,
                        rate=self.args.samplerate,
                        frames_per_buffer=self.args.chunk,
                        input=True)

        # Store data in chunks for 3 seconds
        frame_cntr = 0        
        chunk = self.args.chunk
        time_frame = self.args.samplerate / chunk
        self.start_time = time.time()
        active = True
        while active:
            frames = []
            chunks_in_capture = time_frame*self.capture_buffer_width
            for i in range(0, int(chunks_in_capture)):
                if self.__is_aborted():
                    status = "Aborted : {}".format(datetime.now())
                    print(status)
                    log.info(status)
                    active = False
                    break                
                frame_cntr += 1 
                self.framecount_callback(frame_cntr)
                data = stream.read(chunk)
                frames.append(data)
            self.buffer.put(frames)
            self.new_data.set()
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        self.rec_proc.terminate()
    
    
    """
        enable recording controls the capture thread.
    """
    def enable_recording(self):
        try:
            self.framecount_callback(0)       
            log.info("->INPUT-DEVICE-AQUIRED")
            self.recThread = Thread(name="CAPTURE", target=self.__start_capture)
            self.recThread.start()
                       
        except KeyboardInterrupt:
            self.aborted.set()
            log.info("->ABORT-EXIT")
            print('\nRecording finished')
            self.recThread.join()
                
    def stop_recording(self):
        self.aborted.set()
        self.recThread.join()
        
    
    def dump_recording_to_file(self):
        # Save the recorded data as a WAV file
        wf = wave.open(self.sound_file, 'wb')
        wf.setnchannels(self.args.channels)
        wf.setsampwidth(self.rec_proc.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.args.samplerate)
        frames = self.buffer.get()
        wf.writeframes(b''.join(frames))
        self.sound_file.seek(0)
        wf.close()
    
    def return_recording_as_file(self):
        # Save the recorded data as a WAV file
        tmp_file = io.BytesIO()
        wf = wave.open(tmp_file, 'wb')
        wf.setnchannels(self.args.channels)
        wf.setsampwidth(self.rec_proc.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.args.samplerate)
        frames = self.buffer.get()
        wf.writeframes(b''.join(frames))
        tmp_file.seek(0)
        wf.close()
        bytes_obj = tmp_file.getvalue() 
        return bytes_obj
    
                
        
    def playback_recording(self,frames,progress_callback):
        wf = wave.open(self.sound_file, 'rb')
        # Create an interface to PortAudio
        # Open a .Stream object to write the WAV file to
        # 'output = True' indicates that the sound will be played rather than recorded
        stream = self.rec_proc.open(format = self.rec_proc.get_format_from_width(wf.getsampwidth()),
                        channels = wf.getnchannels(),
                        rate = wf.getframerate(),
                        output = True)
        cntr = 0
        while cntr < frames:
            progress_callback(cntr,frames,status='PLAYBACK')
            data = wf.readframes(self.args.chunk)
            stream.write(data)
            cntr += 1
        progress_callback(cntr,frames,status='DONE    ')
        # Cleanup and rewind file pointer
        stream.close()
        self.sound_file.seek(0)
        progress_callback(0,frames,status='REWINDED')
        wf.close()
        self.rec_proc.terminate()
        
    