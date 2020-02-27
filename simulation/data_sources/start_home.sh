#!/bin/bash
: '
    ** Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Quynh Nguyen and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

echo 'Automatically run the data streamer'
python3 -u ds_test.py 
