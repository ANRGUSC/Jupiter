#!/bin/bash

if [ $# -eq 0 ]
then
    echo "Usage: ./Master-TeraSort.sh Num_Worker"
    echo "Ex: ./Master-TeraSort.sh 5"
    exit
fi

echo "// Send TeraSort to every Worker"
for (( i = 1; i <= $1; i++ ))
do
    sshpass -p 'PASSWORD' scp -o StrictHostKeyChecking=no ./TeraSort n$i:TeraSort/
    sshpass -p 'PASSWORD' scp -o StrictHostKeyChecking=no ./CodedTeraSort n$i:TeraSort/
done

    
