#################################################
# Veholt gårdsbryggeri, LP og kassett lydinsamler.
# Brukerkontroll
#################################################
import os
from datetime import datetime
#################################################
#Remote Control
#################################################
zmq_port = 5555
ip_addr_local='127.0.0.1'
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


