#################################################
# Veholt gårdsbryggeri, LP og kassett lydinsamler.
# Brukerkontroll
#################################################
import os
from datetime import datetime
#################################################
#Remote Control
#################################################
run_mode = ["run","test","debug"]
zmq_proto_ip = 'tcp://*'
zmq_port_pubsub = '3739'
zmq_port_reqrep = '3740'
zmq_topics_list = ["timewindow" , "fft_window" , "rms" ]

default_save_dir = 'raw_recording'
starttime = datetime.now()
timestamp = datetime.timestamp(starttime)

#################################################
# Signal Processing Settings
#################################################
sample_rate = 441000
packet_size = 384
np_array_dim = 13

#################################################
# QT Gui Settings
#################################################
sample_rate = 44100
ADC_bits = 16
rms_window = 2048
t_start = 0
t_stop = 100e-3

#################################################
# ZMQ Device
#################################################
zmq_port_producer_streamer = '5559'
zmq_port_streamer_worker = '5560'