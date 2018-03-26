#!/bin/bash

if [ $# -lt 2 ]
then
    echo "Usage: ./Master-Run-TeraSort.sh K"
    echo "Ex: ./Master-Run-TeraSort 16"
    exit
fi

make

echo "// Experiment K = $1"
echo "// Rate limit: $2 Mbps"
host="localhost"
for (( i = 1; i <= $1; i++ ))
do
    host="$host,n$i"
    scp ./TeraSort n$i:/root/TeraSort/
done


echo ""
echo ""
echo "// Run TeraSort"    
mpirun --allow-run-as-root -mca btl ^openib --mca btl_tcp_if_include eth0 --mca oob_tcp_if_include eth0 -host $host --mca plm_rsh_no_tree_spawn 1 ./TeraSort


for (( i = 1; i <= $1; i++ ))
do
    scp n$i:/root/TeraSort/Output/countIPs.txt ~/TeraSort   
    cp countIPs.txt countIPs_$i.txt
    rm countIPs.txt
    cat countIPs_$i.txt >> tempOutput.txt
done

mv tempOutput.txt ~/TeraSort/Intermediate/countIPs.txt

./filterResult ~/TeraSort/Intermediate/countIPs.txt ~/TeraSort/Output/result.txt $2
