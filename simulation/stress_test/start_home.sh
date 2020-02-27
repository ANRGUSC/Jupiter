#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Quynh Nguyen and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

echo 'Automatically run the CPU checking'
python3 -u cpu_test.py 

echo 'Automatically run the stress test'
python3 -u keep_alive.py
