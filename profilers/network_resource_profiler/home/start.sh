#!/bin/bash
: '
    ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
    **     contributor: Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari
    **     Read license file in main directory for more details
'

service ssh start

echo 'Installing and starting mongodb'
/network_profiling/central_mongod start

# Kubernetes will inject environment variables into a container based on your
# deployment configurations. We inject the hostnames of the child nodes and the
# task in which the container is responsible for.
echo "the available nodes are:"
echo $ALL_NODES
echo "their IPs are:"
echo $ALL_NODES_IPS
echo "my node is:"
echo $SELF_NAME

# Read env vars into arrays
read -a nodes <<<${ALL_NODES//:/ }
read -a nodes_ips <<<${ALL_NODES_IPS//:/ }

# Check if lengths are equal
if [ ${#nodes[@]} -ne ${#nodes_ips[@]} ]; then
    echo "Something is wrong with the environment variables!"
fi

# ALL_NODES lists the host names and ALL_NODES_IPS lists the ip address of the
# nodes ':'. Since we are using Kubernetes, we use customized hostnames
# (managed by the k8s dns) to address pods in the cluster.
# The hostnames correspond to the node name the profiler will run on.
for ((i = 0; i < ${#nodes[@]}; i++)); do
    INPUT_ARGS="${nodes[i]},${nodes_ips[i]},PASSWORD"
    echo $INPUT_ARGS >> /network_profiling/central_input/nodes.txt
    INPUT_ARGS_2="${nodes_ips[i]}"
    echo $INPUT_ARGS_2 >> /resource_profiling/ip_path
done

cat /resource_profiling/ip_path

echo 'Generate the list of links'
python3 -u /network_profiling/generate_link_list.py

python3 -u /resource_profiling/job.py &

echo 'Automatically run the central network scheduler'
python3 -u /network_profiling/central_scheduler.py




