import os
import argparse
import queue
import sys
import time
from PyQt5 import QtWidgets, uic
import sounddevice as sd
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)
import app.usb_collector as process_class
import app.config as config
import app.qtgui_functions as qt_functions
import zmq


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
    data_list = []
    for i in range(array_count):
        data_list.append(s.recv_pyobj())
    data_2Dnumpy = numpy.asarray(data_list)
    data = flatten1D(data_2Dnumpy)
    # -------------------------------------------------------------------------------------------------------------------
    #   Create QTGui for inspecting recording
    # -------------------------------------------------------------------------------------------------------------------

    app = QtWidgets.QApplication([])
    gui = qt_functions.QTGuiFunctions(config=config)
    t_stop = len(data)/config.sample_rate
    gui.set_plottime(0,t_stop,len(data))
    print("Number of time points : %i " % len(gui.get_plottime()))
    gui.set_data(data)
    gui.graphWidget.setTitle("ZMQ Test")
    gui.update_plot()
    gui.show()
    sys.exit(app.exec_())

    print("   Done.")
    #    while True:
    #       print("service started")
    #      time.sleep(1)

    parser.exit(0)


def flatten1D(array_2d):
    N_dim,M_dim = array_2d.shape
    O_dim = N_dim * M_dim
    return array_2d.reshape(O_dim)







if __name__ == "__main__":
    main()