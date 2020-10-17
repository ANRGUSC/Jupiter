#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

echo 'Installing and starting mongodb'
/jupiter/central_mongod start




# Kubernetes will inject environment variables into a container based on your
# deployment configurations. We inject the hostnames of the child nodes and the
# task in which the container is responsible for.
echo "the available nodes are:"
echo $ALL_NODE_NAMES
echo "their IPs are:"
echo $ALL_NODE_IPS
echo "my node is:"
echo $NODE_NAME
echo "my IP is:"
echo $NODE_IP
echo "home node IP is:"
echo $HOME_NODE_IP

echo '---------------Step 2 - Generating random test files--------------------'
/jupiter/droplet_generate_random_files $NODE_IP


# Read env vars into arrays
read -a nodes <<<${ALL_NODE_NAMES//:/ }
read -a nodes_ips <<<${ALL_NODE_IPS//:/ }
read -a home_ip <<<${HOME_NODE_IP//:/ }

# Check if lengths are equal
if [ ${#nodes[@]} -ne ${#nodes_ips[@]} ]; then
    echo "Something is wrong with the environment variables!"
fi

echo $nodes
echo $nodes_ips
echo $home_ip


# ALL_NODES lists the host names and ALL_NODES_IPS lists the ip address of the
# nodes ':'. Since we are using Kubernetes, we use customized hostnames
# (managed by the k8s dns) to address pods in the cluster.
# The hostnames correspond to the node name the profiler will run on.


INPUT_ARGS="home,${home_ip},NA"
echo $INPUT_ARGS >> /jupiter/central_input/nodes.txt



for ((i = 0; i < ${#nodes[@]}; i++)); do
    INPUT_ARGS="${nodes[i]},${nodes_ips[i]},NA"
    echo $INPUT_ARGS >> /jupiter/central_input/nodes.txt
done

echo 'Generate the list of links'
python3 -u /jupiter/generate_link_list.py

echo 'Automatically run the central network scheduler'
python3 -u /jupiter/central_scheduler.py &

python3 -u /jupiter/keep_alive.py


