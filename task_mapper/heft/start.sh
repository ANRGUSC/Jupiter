#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

# echo "my profiler IDs are:"
# echo $PROFILERS
# echo "my execution home IP is"
# echo $EXECUTION_HOME_IP

echo '-------------------------------------'
echo 'Automatically generating HEFT input'
python3 -u read_input_heft.py &
python3 -u write_input_heft.py &


echo '-------------------------------------'
echo 'Perform HEFT scheduling'

python -u master.py &
python3 -u keep_alive.py




