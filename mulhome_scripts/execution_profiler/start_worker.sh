#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Pradipta Ghosh, Quynh Nguyen, and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'
service ssh start

python3 -u get_files.py &
sleep infinity