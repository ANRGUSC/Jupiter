#!/bin/bash

service ssh start

python3 -u get_files.py &
# python3 -u profiler.py &
python3 -u keepalive.py

