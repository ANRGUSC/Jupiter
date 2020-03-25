#!/bin/bash

service ssh start

# TODO: Pods address other pods via the target pod's service IP and service 
# port. Currently, the port is hardcoded at 5000 (i.e. it does not use the 
# default port 22). Need a more flexible structure for changing port numbers 
# (another environment variable?). If we move to protobufs, we can instead get 
# rid of SSHD.

# Run python with '-u' for unbuffered prints so the Kubernetes log system gets
# all the print statements.
# 

echo 'Installing and starting mongodb'
./central_mongod start

echo 'Starting the evaluation'
python3 -u evaluate.py &


echo 'Starting the scheduler'
python3 -u scheduler.py

