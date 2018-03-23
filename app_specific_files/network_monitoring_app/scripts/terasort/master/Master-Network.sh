#!/bin/bash

if [ $# -eq 0 ]
then
    echo "Usage: ./Master-Network.sh Num_Worker"
    echo "Ex: ./Master-Network.sh 5"
    exit
fi

echo "// Backup hosts"
sudo cp /etc/hosts /etc/hosts_backup

echo "// Setup Worker IP"

numWorker=0  # read IP addresses from ips.txt and add them to etc/hosts with index n1, n2, ...
while IFS='' read -r line || [[ -n "$line" ]]; do
    echo "Text read from file: $line"
    numWorker=`expr $numWorker + 1`
    echo "$line n$numWorker" | sudo tee --append /etc/hosts
done < "$2"


echo "// Generate RSA key for seamless ssh"
rm ~/.ssh/*
bash -c "ssh-keygen -t rsa -f ~/.ssh/id_rsa -N ''"

echo "// Setup all Workers"
for (( i = 1; i <= $1; i++ ))
do
    bash -c "cat ~/.ssh/id_rsa.pub | sshpass -p 'PASSWORD' ssh n$i -o StrictHostKeyChecking=no 'cat - >> ~/.ssh/authorized_keys'"
done
