#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Flask server for the master execution profiler to start the execution 
    profilers at the worker nodes
"""
__author__ = "Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import json
import os
from flask import Flask
import configparser
import logging

logging.basicConfig(level=logging.INFO)
JUPITER_CONFIG_INI = '/jupiter/build/jupiter_config.ini'

app = Flask(__name__)


def start():
    os.system("python3 -u profiler_worker.py &")
    logging.info("Started the profiler")

    # return empty dict
    js = json.dumps({})
    return js


app.add_url_rule('/', 'start', start)


def main():
    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI)

    portStr = config['PORT']['FLASK_DOCKER']

    logging.debug("Starting Flask server for remote starting of worker")
    app.run(host='0.0.0.0', port=int(portStr))


if __name__ == '__main__':
    main()
