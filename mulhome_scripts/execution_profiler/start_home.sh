#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Pradipta Ghosh, Quynh Nguyen, and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

echo 'Installing and starting mongodb'
mongod --bind_ip_all &

echo 'Automatically run the scheduler'

python3 -u profiler_home.py &
sleep infinity