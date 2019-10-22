import os
import argparse
import queue
import sys
import time
import sounddevice as sd
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)
import app.usb_collector as process_class
import app.config as config
import zmq
import numpy

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

#TODO Add multiprocessing and start recording process.
#TODO Add Argparser outside of main
#TODO QT plot of realtime data.
#TODO Equalizer and gain control.

def main():
    root_dir = os.path.dirname(__file__)
    default_savedir = os.path.join(root_dir, config.default_save_dir)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-l', '--list-devices', action='store_true',
        help='show list of audio devices and exit')
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        'filename', nargs='?', metavar='FILENAME',
        help='audio file to store recording to')
    parser.add_argument(
        '-d', '--device', type=int_or_str,
        help='input device (numeric ID or substring)')
    parser.add_argument(
        '-r', '--samplerate', type=int, help='sampling rate')
    parser.add_argument(
        '-c', '--channels', type=int, default=1, help='number of input channels')
    parser.add_argument(
        '-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
    args = parser.parse_args(remaining)
    #Start sampling process from input arguments
    q = queue.Queue()
    #recording_process= process_class.USBCollector(queue=q,packet_size=config.packet_size, parser=parser, args=args, rec_folder=default_savedir )
    #recording_process.daemon = True
    #recording_process.start()
    print("Recording Process started")
    #-------------------------------------------------------------------------------------------------------------------
    #   Create ZMQ Subscriber Context
    # -------------------------------------------------------------------------------------------------------------------
    connect_to = 'tcp://127.0.0.1:5000'
    array_count = 10
    ctx = zmq.Context()
    s = ctx.socket(zmq.SUB)
    s.connect(connect_to)
    print("   Done.")
    s.setsockopt(zmq.SUBSCRIBE, b'')
    for i in range(array_count):
        a = s.recv_pyobj()
        
    print("   Done.")
    parser.exit(0)

#    while True:
#       print("service started")
#      time.sleep(1)







if __name__ == "__main__":
    main()