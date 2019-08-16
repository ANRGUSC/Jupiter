# #!/bin/bash


# Run python with '-u' for unbuffered prints so the Kubernetes log system gets
# all the print statements.
# 

echo 'Starting circe home'
python -u /scheduler.py

