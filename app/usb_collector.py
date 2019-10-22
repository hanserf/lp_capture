import time
import sys
import numpy as np
import multiprocessing
import sqlite3
import re
import tempfile
import queue
import sys

import sounddevice as sd
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)


class USBCollector(multiprocessing.Process):
    def __init__(self,queue, packet_size, args, parser):
        super(USBCollector, self).__init__()
        self.packet_size = packet_size
        self.q = queue
        self.args = args
        self.parser = parser


    def run(self) -> None:
        try:
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
                    max_packet_len = 0;
                    while True:
                        raw_data = q.get()
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

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(indata.copy())
