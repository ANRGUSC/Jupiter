"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""

# -*- coding: utf-8 -*-
# Source http://flask.pocoo.org/docs/0.12/patterns/fileuploads/
# 
import json
import sys


import os
from os import path

from flask import Flask, request, redirect, url_for
from flask import send_from_directory
import configparser

"""
Load the Configuration File
"""
HERE     = path.abspath(path.dirname(__file__)) + "/"
INI_PATH = HERE + 'jupiter_config.ini'

config = configparser.ConfigParser()
config.read(INI_PATH)

EXC_FPORT = config['PORT']['FLASK_DOCKER']



app = Flask(__name__)
"""
    Flash server for the master execution profiler to start the execution 
    profilers at the worker nodes
"""
@app.route('/') # Send local stats
def performance():
    data = {}
    os.system("python3 -u profiler.py &")
    print("Started the profiler")

    js = json.dumps(data)
    return js

if __name__ == '__main__':
    print("starting Flask")
    app.run(host='0.0.0.0', port = int(EXC_FPORT))