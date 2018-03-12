"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pranav Sakulkar
 *      Pradipta Ghosh
 *      Jiatong Wang
 *      Aleksandra Knezevic
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""


# -*- coding: utf-8 -*-
# Source http://flask.pocoo.org/docs/0.12/patterns/fileuploads/
# 
import json
import sys


import os
from flask import Flask, request, redirect, url_for
from flask import send_from_directory

app = Flask(__name__)

@app.route('/') # Send local stats
def performance():
    data = {}
    os.system("python3 -u profiler.py &")
    print("Started the profiler")

    js = json.dumps(data)
    return js

if __name__ == '__main__':
    print("starting Flask")
    app.run(host='0.0.0.0', port = 8888)