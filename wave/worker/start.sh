#!/bin/bash


# Run python with '-u' for unbuffered prints so the Kubernetes log system gets
# all the print statements.
# 

echo 'Starting worker node'
python -u /child_appointment.py 8080