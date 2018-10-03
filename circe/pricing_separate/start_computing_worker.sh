#!/bin/bash

service ssh start

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

# Run python with '-u' for unbuffered prints so the Kubernetes log system gets
# all the print statements.
python3 -u centralized_scheduler/pricing_calculator.py &

python3 -u centralized_scheduler/keep_alive.py
