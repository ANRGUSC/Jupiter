#!/bin/bash

service ssh start

# Run python with '-u' for unbuffered prints so the Kubernetes log system gets
# all the print statements.
python3 -u circe.py

# if circe quits
sleep infinity
