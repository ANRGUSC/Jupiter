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
    scp ./TeraSort n$i:TeraSort/
    scp ./CodedTeraSort n$i:TeraSort/
done

    
