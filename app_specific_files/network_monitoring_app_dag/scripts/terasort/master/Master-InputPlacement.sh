#!/bin/bash

if [ $# -eq 0 ]
then
    echo "Usage: ./Master-InputPlacement.sh Num_Worker"
    echo "Ex: ./Master-InputPlacement.sh 5"
    exit
fi

host="localhost"
for (( i = 1; i <= $1; i++ ))
do
    echo $i
    host="$host,n$i"
    sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no n$i 'rm -rf ~/TeraSort/Intermediate; mkdir -p ~/TeraSort/Intermediate'
    sshpass -p 'PASSWORD' scp -o StrictHostKeyChecking=no ./InputPlacement n$i:TeraSort/
done

mpirun -mca btl ^openib --mca btl_tcp_if_include eth0 --mca oob_tcp_if_include eth0 -host $host --mca plm_rsh_no_tree_spawn 1 ./InputPlacement
mpirun -mca btl ^openib --mca btl_tcp_if_include eth0 --mca oob_tcp_if_include eth0 -host $host --mca plm_rsh_no_tree_spawn 1 ./InputPlacement code
