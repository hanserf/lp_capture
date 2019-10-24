"""A test that publishes NumPy arrays.
Currently the timing of this example is not accurate as it depends on the
subscriber and publisher being started at exactly the same moment. We should
use a REQ/REP side channel to synchronize the two processes at the beginning.
"""

#
#    Copyright (c) 2010 Brian E. Granger
#
#    This file is part of pyzmq.
#
#    pyzmq is free software; you can redistribute it and/or modify it under
#    the terms of the Lesser GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyzmq is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    Lesser GNU General Public License for more details.
#
#    You should have received a copy of the Lesser GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import time
import random
import zmq
import numpy
#TODO Wrap this up in a class. Make it possible to spawn multiple publishers with topics.
#TODO Define topics in config. Topics will be signal processing related.
#TODO Subscriptions to topics and topic generation should be enabled from qtgui
import app.config as config
def main():
    run_mode = config.run_mode[1]
    bind_to = config.zmq_setup
    array_size = 192
    ctx = zmq.Context()
    s = ctx.socket(zmq.PUB)
    s.bind(bind_to)

    print ("Waiting for subscriber to connect...")
    # We need to sleep to allow the subscriber time to connect
    time.sleep(1.0)
    print ("   Done.")

    print ("Entring run mode %s" % run_mode)

    if run_mode == 'test':
        try:
            while True:
                a = numpy.random.rand(array_size)
                s.send_pyobj(a)
                print("Sending")
                delay_lower_limit = 900
                delay_high_limit = 1000
                timeDelay = random.randrange(delay_lower_limit, delay_high_limit)
                time.sleep(0.2)

        except KeyboardInterrupt:
            print('Quitting ZMQ Subscriber')
            s.close()
            ctx.destroy()
            exit(0)
    else:
        print("No other run modes defined")
        exit(0)


if __name__ == "__main__":
    main()