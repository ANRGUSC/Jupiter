#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Pradipta Ghosh, Quynh Nguyen, Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

echo '---------------Step 1 - Installing and starting mongodb----------------'
/jupiter/droplet_mongod start

echo '---------------Step 2 - Generating random test files--------------------'
# my_ip=$SELF_IP
# echo $my_ip
# The SELF_IP environment variable contains the ip of the k8 service
/jupiter/droplet_generate_random_files $NODE_IP
echo '-------------------------------------------------------------------'

echo 'Step 4 -  Prepare MongoDB database, Automatically run measurement and regression script'

python3 -u /jupiter/automate_droplet.py $NODE_IP &

python3 -u /jupiter/get_schedule.py &

python3 -u /jupiter/keep_alive.py







