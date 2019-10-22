import time
import sys
import numpy as np
import multiprocessing
import tempfile
import sys
import os
import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)


class USBCollector(multiprocessing.Process):
    def __init__(self,queue, packet_size, args, parser, rec_folder):
        super(USBCollector, self).__init__()
        self.packet_size = packet_size
        self.q = queue
        self.args = args
        self.parser = parser
        self.recording_folder = rec_folder


    def run(self) -> None:
        print("Entering Recording loop")
        try:
            self.check_if_folder_exists()
            self.change_folder_path()
            if self.args.samplerate is None:
                device_info = sd.query_devices(self.args.device, 'input')
                # soundfile expects an int, sounddevice provides a float:
                self.args.samplerate = int(device_info['default_samplerate'])
            if self.args.filename is None:

                self.args.filename = tempfile.mktemp(prefix='delme_rec_unlimited_',
                                                suffix='.wav', dir='')

            # Make sure the file is opened before recording anything:
            with sf.SoundFile(self.args.filename, mode='x', samplerate=self.args.samplerate,
                              channels=self.args.channels, subtype=self.args.subtype) as file:
                with sd.InputStream(samplerate=self.args.samplerate, device=self.args.device,
                                    channels=self.args.channels, callback=self.callback):
                    print('#' * 80)
                    print('press Ctrl+C to stop the recording')
                    print('#' * 80)
                    samp_cntr = 0
                    max_packet_len = 0
                    while True:
                        raw_data = self.q.get()
                        file.write(raw_data)
                        samp_cntr += 1
                        packet_len = len(raw_data)
                        new_max = self.find_max_packet_len(packet_len, max_packet_len)
                        max_packet_len = new_max
                        if samp_cntr % max_packet_len == 0:
                            print("Raw data type %s " % type(raw_data) + ", Raw data length %f" % len(
                                raw_data) + " , max payload length = %i " % max_packet_len)
        except KeyboardInterrupt:
            print('\nRecording finished: ' + repr(self.args.filename))
            self.q.parser.exit(0)
        except Exception as e:
            self.q.parser.exit(type(e).__name__ + ': ' + str(e))

    def find_max_packet_len(self, a_packet, known_max):
        if (a_packet > known_max):
            return a_packet
        else:
            return known_max

    def check_if_folder_exists(self):
        if not os.path.exists(self.recording_folder):
            self.make_folder()
        else:
            print("Recording folder exists")

    def make_folder(self):
        # Make folder for Interesting images
        try:
            os.mkdir(self.recording_folder)
        except OSError:
            print("Creation of directory %s failed" % self.recording_folder)
            exit(1)
        else:
            print("Successfully created Recording directory %s " % self.recording_folder)

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(indata.copy())

    def change_folder_path(self):
        try:
            os.chdir(self.recording_folder)
        except OSError:
            print("Failed Changing directory path to %s: " % self.recording_folder)
            exit(1)
        else:
            print("Changing directory path to  %s " % self.recording_folder)
