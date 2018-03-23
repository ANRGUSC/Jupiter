#!/bin/bash

if [ $# -lt 2 ]
then
    echo "Usage: ./Master-Run-CodedTeraSort.sh K"
    echo "Ex: ./Master-Run-CodedTeraSort 16"
    exit
fi

make

echo "// Experiment K = $1 workers"
host="localhost"
for (( i = 1; i <= $1; i++ ))
do
    host="$host,n$i"
    scp ./CodedTeraSort n$i:/root/TeraSort/    
done


echo ""
echo ""
echo "// Run TeraSort"    
mpirun --allow-run-as-root -mca btl ^openib --mca btl_tcp_if_include eth0 --mca oob_tcp_if_include eth0 -host $host --mca plm_rsh_no_tree_spawn 1 ./CodedTeraSort

for (( i = 1; i <= $1; i++ ))
do
    scp n$i:/root/TeraSort/Output/countIPs-C.txt ~/TeraSort
    mv countIPs-C.txt countIPs-C_$i.txt
    cat countIPs-C_$i.txt >> tempOutput-C.txt
done

mv tempOutput-C.txt ~/TeraSort/Intermediate/countIPs-C.txt

./filterResult ~/TeraSort/Intermediate/countIPs-C.txt ~/TeraSort/Output/result-C.txt $2
