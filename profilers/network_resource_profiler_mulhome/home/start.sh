#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

echo 'Installing and starting mongodb'
/network_profiling/central_mongod start

echo '---------------Step 2 - Generating random test files--------------------'
/network_profiling/droplet_generate_random_files $SELF_IP


# Kubernetes will inject environment variables into a container based on your
# deployment configurations. We inject the hostnames of the child nodes and the
# task in which the container is responsible for.
echo "the available nodes are:"
echo $ALL_NODES
echo "their IPs are:"
echo $ALL_NODES_IPS
echo "my node is:"
echo $SELF_NAME
echo "my IP is:"
echo $SELF_IP
echo "all home list IP is:"
echo $HOME_IP
echo "all home list ID is:"
echo $HOME_ID

# Read env vars into arrays
read -a nodes <<<${ALL_NODES//:/ }
read -a nodes_ips <<<${ALL_NODES_IPS//:/ }
read -a home_ids <<<${HOME_ID//:/ }
read -a home_ips <<<${HOME_IP//:/ }

# Check if lengths are equal
if [ ${#nodes[@]} -ne ${#nodes_ips[@]} ]; then
    echo "Something is wrong with the environment variables!"
fi

echo $nodes
echo $nodes_ips
echo $home_ids
echo $home_ips


# ALL_NODES lists the host names and ALL_NODES_IPS lists the ip address of the
# nodes ':'. Since we are using Kubernetes, we use customized hostnames
# (managed by the k8s dns) to address pods in the cluster.
# The hostnames correspond to the node name the profiler will run on.

for ((i = 0; i < ${#home_ids[@]}; i++)); do
    INPUT_ARGS="${home_ids[i]},${home_ips[i]},NA"
    echo $INPUT_ARGS >> /network_profiling/central_input/nodes.txt
    # INPUT_ARGS_2="${home_ips[i]}"
    # echo $INPUT_ARGS_2 >> /resource_profiling/ip_path
done


for ((i = 0; i < ${#nodes[@]}; i++)); do
    INPUT_ARGS="${nodes[i]},${nodes_ips[i]},NA"
    echo $INPUT_ARGS >> /network_profiling/central_input/nodes.txt
    # INPUT_ARGS_2="${nodes_ips[i]}"
    # echo $INPUT_ARGS_2 >> /resource_profiling/ip_path
done

echo 'Generate the list of links'
python3 -u /network_profiling/generate_link_list.py

echo 'Automatically run the central network scheduler'
python3 -u /network_profiling/central_scheduler.py &

python3 -u /network_profiling/keep_alive.py


