#!/bin/bash

echo "// Install SSH and Emacs"
sudo apt-get update
sudo apt-get install emacs24-nox -y
sudo apt-get install ssh rsync -y

echo "// Install Hadoop for Teragen"
sudo apt-get install openjdk-9-jre-headless -y
wget http://supergsego.com/apache/hadoop/common/hadoop-2.8.1/hadoop-2.8.1.tar.gz -P ~/
tar -zxvf ~/hadoop-2.8.1.tar.gz -C ~/

echo "// Install Compiler and Open MPI"
sudo apt-get install g++ make openmpi-bin libopenmpi-dev -y
