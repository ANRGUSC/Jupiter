#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

python3.6 -u read_input_heft.py &
python3.6 -u write_input_heft.py &
python3.6 -u master_heft.py &

# keepalive to debug upon failures
sleep infinity