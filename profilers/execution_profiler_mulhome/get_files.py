#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
	Flash server for the master execution profiler to start the execution 
	profilers at the worker nodes
"""
__author__ = "Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"


# Source http://flask.pocoo.org/docs/0.12/patterns/fileuploads/

import json
import sys
import os
from os import path

from flask import Flask, request, redirect, url_for
from flask import send_from_directory
import configparser

app = Flask(__name__)

def performance():
	"""Send local stats
	
	Returns:
		json: local stats
	"""
	data = {}
	os.system("python3 -u profiler.py &")
	print("Started the profiler")

	js = json.dumps(data)
	return js
app.add_url_rule('/', 'performance', performance)

def main():
	"""
	Load the Configuration File
	"""
	HERE     = path.abspath(path.dirname(__file__)) + "/"
	INI_PATH = HERE + 'jupiter_config.ini'

	config = configparser.ConfigParser()
	config.read(INI_PATH)

	global EXC_FPORT
	
	EXC_FPORT = config['PORT']['FLASK_DOCKER']

	print("starting Flask")
	app.run(host='0.0.0.0', port = int(EXC_FPORT))

if __name__ == '__main__':
	main()