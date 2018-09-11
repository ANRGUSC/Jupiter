#!/bin/bash

service ssh start

# Kubernetes will inject environment variables into a container based on your
# deployment configurations. We inject the hostnames of the child nodes and the
# task in which the container is responsible for.
echo "my child nodes are:"
echo $CHILD_NODES
echo "their IPs are:"
echo $CHILD_NODES_IPS
echo "my task is:"
echo $TASK

echo "flag is:"
echo $FLAG
echo "number of inputs for my task:"
echo $INPUTNUM

# Read env vars into arrays
read -a children <<<${CHILD_NODES//:/ }
read -a children_ips <<<${CHILD_NODES_IPS//:/ }

# Read env vars into arrays
read -a nodes <<<${ALL_NODES//:/ }
read -a nodes_ips <<<${ALL_NODES_IPS//:/ }

# Check if lengths are equal
if [ ${#nodes[@]} -ne ${#nodes_ips[@]} ]; then
    echo "Something is wrong with the environment variables!"
fi


# Check if lengths are equal
if [ ${#children[@]} -ne ${#children_ips[@]} ]; then
    echo "Something is wrong with the environment variables!"
fi

# CHILD_NODES lists the ip address of the children nodes delimited by ':'. Since
# we are using Kubernetes, we use customized hostnames (managed by the k8s dns)
# to address pods in the cluster. The hostnames correspond to the task number 
# the child nodes will run.
for ((i = 0; i < ${#children[@]}; i++)); do
    INPUT_ARGS="$INPUT_ARGS ${children[i]} ${children_ips[i]} root PASSWORD"
done

echo "monitor.py input args are:"
echo $INPUTNUM $FLAG $INPUT_ARGS

# TODO: Pods address other pods via the target pod's service IP and service 
# port. Currently, the port is hardcoded at 5000 (i.e. it does not use the 
# default port 22). Need a more flexible structure for changing port numbers 
# (another environment variable?). If we move to protobufs, we can instead get 
# rid of SSHD.

# monitor.py input structure:
#   child1_task_num child1_ip child1_user child1_pw child2_task_num child2_ip child2_user child2_pw my_task
echo "python3 centralized_scheduler/monitor.py $INPUTNUM $FLAG $INPUT_ARGS $TASK"

# Run python with '-u' for unbuffered prints so the Kubernetes log system gets
# all the print statements.
python3 -u centralized_scheduler/monitor.py $INPUTNUM $FLAG $INPUT_ARGS $TASK
