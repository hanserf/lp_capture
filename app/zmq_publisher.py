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

import zmq
import numpy

def main():

    bind_to = 'tcp://127.0.0.1:5000'
    array_size = 192
    array_count = 10
    ctx = zmq.Context()
    s = ctx.socket(zmq.PUB)
    s.bind(bind_to)

    print ("Waiting for subscriber to connect...")
    # We need to sleep to allow the subscriber time to connect
    time.sleep(1.0)
    print ("   Done.")

    print ("Sending arrays...")
    for i in range(array_count):
        a = numpy.random.rand(array_size)
        s.send_pyobj(a)
    print ("   Done.")

if __name__ == "__main__":
    main()