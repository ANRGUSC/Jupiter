#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Pradipta Ghosh, Quynh Nguyen, and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

echo 'Installing and starting mongodb'
/central_mongod start

cp sample_input/1botnet.ipsum generated_files/25botnet.ipsum

echo 'Automatically run the scheduler'

python3 -u profiler_home.py &
python3 -u keep_alive.py