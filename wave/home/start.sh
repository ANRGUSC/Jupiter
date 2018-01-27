#!/bin/bash


# Run python with '-u' for unbuffered prints so the Kubernetes log system gets
# all the print statements.
# 

echo 'Starting home or master node'
python -u /master.py 8080