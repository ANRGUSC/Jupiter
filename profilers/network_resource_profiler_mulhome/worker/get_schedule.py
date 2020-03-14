"""
.. note:: This is the main script to run in every node in the system for network profiling procedure.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import random
import subprocess
import pyinotify
from apscheduler.schedulers.background import BackgroundScheduler
import os
import csv
import paramiko
from scp import SCPClient
from pymongo import MongoClient
import datetime
import pandas as pd
import numpy as np
import time
import sys
from os import listdir
from os.path import isfile, join
from os import path
import configparser
import requests


sys.path.append("../")

def main():
    """ Start polling the profiler home to request the ``scheduling`` file. If succeed, stop the process.
    """

    INI_PATH = '/network_profiling/jupiter_config.ini'

    config = configparser.ConfigParser()
    config.read(INI_PATH)

    FLASK_SVC    = int(config['PORT']['FLASK_SVC'])
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
    SELF_IP = os.environ["SELF_IP"]
    HOME_IP = os.environ["HOME_IP"]

    flag_schedule = "False"
    home_ips = HOME_IP.split(':')
    home_ips = home_ips[1:]
    while flag_schedule == "False":
        time.sleep(10)
        try:
            for home_ip in home_ips:
                print("get the schedule from http://"+ home_ip + ":" + str(FLASK_SVC))
                line = "http://"+home_ip+":" + str(FLASK_SVC) + "/schedule/" + SELF_IP
                r = requests.get(line).json()
                if len(r):
                    flag_schedule = r["status"]
        except Exception as e:
            print("Scheduler request failed. Will try again, details: " + str(e))


if __name__ == '__main__':
    main()



