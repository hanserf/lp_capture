from cmd import Cmd
from pyfiglet import Figlet
import io
import os
import gzip
import argparse
import logging
import sounddevice as sd
import pkg_resources


#This will put recorded buffer into the tcp server and maintain flow control


    # -------------------------------------------------------------------------------------------------------------------
    #   Create A Process for recording data
    # -------------------------------------------------------------------------------------------------------------------

log = logging.getLogger('Worker')
sw_version = pkg_resources.require("lp_server")[0].version
def control():
    from audio_recorder import AudioRecorder, SoundDeviceError, SoundDeviceStop
    import config as config

    class MyPrompt(Cmd):
        prompt = 'SERVER:>'
        f = Figlet(font='doom')
        print(f.renderText('LP->Capture'))
        global sw_version
        f.setFont(font='small')
        print(f.renderText('Server v{}'.format(sw_version)))
        intro = "Welcome! Type ? to list commands"

        def __init__(self, ):
            super(MyPrompt, self).__init__()
            self.recorder = None
            self.uptime = 0
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

        def __uptime_callback(self,uptime):
            self.uptime = uptime
            
        def help_exit(self):
            print('exit the application. Shorthand: Ctrl-D.')

        def do_exit(self, inp):
            '''exit the application.'''
            print("Caught exit signal, killing application")
            print("Done, Bye")
            raise SystemExit

        do_EOF = do_exit
        help_EOF = help_exit

        
        def do_read(self,inp):
            #compressed = self.shell.read_shell_status(5)
            #print("Compressed Length : {}".format(len(compressed)))
            #data = self.shell.gunzip_bytes_obj(compressed)
            #print("Output len : {}".format(len(data)))
            #print("stdout: \n{}".format(data))
            return True
            
               
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
                    'file', nargs='?', metavar='FILENAME',
                    help='Capture file, Defaults to ram')
                
                parser.add_argument(
                    '-d', '--device', type=self.__int_or_str,
                    help='input device (numeric ID or substring)')
                parser.add_argument(
                    '-r', '--samplerate', type=int, help='sampling rate')
                parser.add_argument(
                    '-c', '--channels', type=int, default=1, help='number of input channels')
                parser.add_argument(
                    '-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
                
                args = parser.parse_known_args()
                args = parser.parse_args(inp.split())    
                if args.list_devices:         
                    print(sd.query_devices()) 
                elif args.buffer_width_s:
                    self.recorder = AudioRecorder(args=args,parser=parser,uptime_callback=self.__uptime_callback)
                    self.recorder.init_sounddevice()
                else:
                    print("Supply buffer width in [s] to start recording")
            except SystemExit:
                print("Resuming")        

        def help_recording(self):
            print("Start recording.")
            print("Input :")
            print("Arg[0] : timeout")
            print("Arg[1] : number of attempts")

        def do_recording(self, inp):
            if self.recorder is None:
                print("Device Not Initialized")
                return False
            cmd = inp.split()
            timeout = int(cmd[0])
            attempts = int(cmd[1])
            self.recorder.enable_recording(timeout=timeout,n_attempts=attempts)
            print("Recording Process started")
            
                        


    MyPrompt().cmdloop()


if __name__ == "__main__":
    from audio_recorder import AudioRecorder, SoundDeviceError, SoundDeviceStop

    control()
