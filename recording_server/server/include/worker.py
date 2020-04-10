from cmd import Cmd
from pyfiglet import Figlet
import io
import time
import os
import gzip
import wave
import logging
import pickle
import sys
import pkg_resources
from threading import Event, Thread
from queue import Queue
from server.include.pyaudio_recorder import pyAudioRecorder

log = logging.getLogger('Worker')
sw_version = pkg_resources.require("lp_server")[0].version

class Worker():
    def __init__(self,e_abort, json_dictionary_callback=None):
        """
            Variables Controlling audio Recording interface
        """
        # External Control
        self.abort = e_abort
        self.file_callback = json_dictionary_callback
        self.use_compression = False
        # Thread Local 
        self.recorder = None 
        self.framecount = 0
        self.rec_window = 0
        self.buffer = Queue()
        self.new_data = Event()
        
    @staticmethod
    def __progress(count, total, status=''):
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))
        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
        sys.stdout.flush()
    @staticmethod
    def gzip_compress(bytes_like):
        filename = io.BytesIO()
        # writing zip file
        with gzip.GzipFile(fileobj=filename, mode= 'wb') as f:
            f.write(bytes_like)
            filename.seek(0, os.SEEK_END)
            size = filename.tell()
            filename.seek(0)
        compressed_binary = filename.getvalue()
        return compressed_binary,size

    @staticmethod
    def gunzip_bytes_obj(bytes_like):
        in_ = io.BytesIO()
        in_.write(bytes_like)
        in_.seek(0)
        with gzip.GzipFile(fileobj=in_, mode='rb') as fo:
            gunzipped_bytes_obj = fo.read()
        return gunzipped_bytes_obj

    def __clear_abort(self):
        self.abort.clear()

    def __framecount_callback(self,cntr):
        self.framecount = cntr
    
    def __is_new_data(self):
        return self.new_data.is_set()

    def __buffer_queue_callback(self,start_time,data_frame):
        res_tuple = (start_time,self.framecount,data_frame)
        self.buffer.put(res_tuple)
        self.new_data.set()

    def init_worker(self,args,parser):
        self.rec_window = args.buffer_width_s[0]
        self.recorder = pyAudioRecorder(args=args,
                                        parser=parser,
                                        e_abort=self.abort,
                                        buf_queue_callback=self.__buffer_queue_callback
                                        )
        self.recorder.init_sounddevice()
    
    def start_recording(self):
        if self.recorder is None:
            print("Device Not Initialized")
            return False
        self.recorder.enable_recording()
        
    def stop_recording(self):
        self.recorder.stop_recording()
    
    def set_use_compression(self, boolean):
        self.use_compression = boolean
    
    
    def file_recording_loop(self):
        """
            This loop will put recorded frames into a wave format file object existing entirely in RAM
            When a new buffer of X frames is ready, they will be converted to Wave and called back to the conrol module.
        """
        enable = True
        cntr = 0
        while enable:
            if self.__is_new_data():
                cntr += 1        
                (start_time,framecount,frames) = self.buffer.get()
                raw_data,size = self.frames_to_file_like(frames)
                if self.use_compression:
                    compressed,size = self.gzip_compress(frames)
                    raw_data = compressed                  
                log.debug("Data Append #{}to file\n Collected size = {}, File Size = {}".format(cntr, size, size))
                self.file_callback(start_time,framecount,self.use_compression,size,raw_data)
                self.new_data.clear()
            else:
                if self.abort.is_set():
                    break
                time.sleep(0.5)

    def stop_rewind_playback(self):
        self.recorder.stop_recording()
        print("Fetching recorded audio, rewinding")
        file_like = self.recording_as_file_like()
        print("framecount = {} ".format(self.framecount))
        self.recorder.playback_recording(file_like=file_like,frames=self.framecount, progress_callback=self.__progress)

    def frames_to_file_like(self,data_frames):
        # Save the recorded data as a WAV file
        args,parser = self.recorder.get_args_parser()
        tmp_file = io.BytesIO()
        wf = wave.open(tmp_file, 'wb')
        wf.setnchannels(args.channels)
        wf.setsampwidth(args.sample_format)
        wf.setframerate(args.samplerate)
        wf.writeframes(b''.join(data_frames))
        tmp_file.seek(0, os.SEEK_END)
        size = tmp_file.tell()
        tmp_file.seek(0)
        wf.close()
        file_like = tmp_file.getvalue()
        return  file_like, size



def test():
    class ControlPrompt(Cmd):
        prompt = 'SERVER:>'
        f = Figlet(font='doom')
        print(f.renderText('LP->Capture'))
        global sw_version
        f.setFont(font='small')
        print(f.renderText('Server v{}'.format(sw_version)))
        intro = "Welcome! Type ? to list commands"

        def __init__(self, ):
            super(ControlPrompt, self).__init__()
            self.abort = Event()
            self.new_data = Event()
            self.worker = Worker(e_abort=self.abort,e_new_data=self.new_data)
            self.readThread = None

        """
            Default Functions for the shell and Argparse
        """

        @staticmethod
        def __int_or_str(text):
            """Helper function for argument parsing."""
            try:
                return int(text)
            except ValueError:
                return text

        def help_exit(self):
            print('exit the application. Shorthand: Ctrl-D.')

        def do_exit(self, inp):
            '''exit the application.'''
            print("Caught exit signal, killing application")
            print("Done, Bye")
            raise SystemExit

        do_EOF = do_exit
        help_EOF = help_exit

        def do_init(self,inp):
            try:
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

            except SystemExit:
                # Printing help raises System Exit!
                print("Resuming \r\n\r\n")

        def help_rec(self):
            print("Start recording.")

        def do_rec(self, inp):
            self.worker.start_recording()
            print("Recording Process started")

        def do_rec_read(self, inp):
            self.worker.start_recording()
            print("Recording Process started")
            self.readThread = Thread(name="READBACK", target=self.worker.readback_loop)
            time.sleep(0.5)
            print("Playback Process started")
            self.readThread.start()

        def help_stop(self):
            print("Stop the recording thread")


        def do_framecount(self, inp):
            print("-->framecount: {}".format(self.worker.framecount))

        def do_abort(self, inp):
            self.abort.set()
            print("Recording aborted set")


        def do_stop_recording(self, inp):
            self.worker.stop_recording()
            print("Recording Stopped")

        def do_stop_rewind_playback(self,inp):
            print("Stopping recorder before playback")
            self.worker.stop_rewind_playback()
new_data
    test()
