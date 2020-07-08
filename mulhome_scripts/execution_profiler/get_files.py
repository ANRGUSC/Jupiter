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

logging.basicConfig(level=logging.DEBUG)
JUPITER_CONFIG_INI = '/jupiter/jupiter_config.ini'

app = Flask(__name__)


def performance():
    """Send local stats

    Returns:
    json: local stats
    """
    data = {}
    os.system("python3 -u profiler.py &")
    logging.debug("Started the profiler")

    js = json.dumps(data)
    return js


app.add_url_rule('/', 'performance', performance)


def main():
    """
    Load the Configuration File
    """
    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI)

    global EXC_FPORT

    EXC_FPORT = config['PORT']['FLASK_DOCKER']

    logging.debug("starting Flask")
    app.run(host='0.0.0.0', port=int(EXC_FPORT))


if __name__ == '__main__':
    main()
