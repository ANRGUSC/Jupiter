"""
.. note:: This is the main script to run in every node in the system for network profiling procedure.
"""

__author__ = "Quynh Nguyen, Pradipta Ghosh, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import requests
import logging

# This exists in a build/ folder created by build_push_exec.py
from build.jupiter_utils import app_config_parser
import configparser
import os
import time

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

"""Paths specific to container (see home.Dockerfile)"""
APP_DIR = "/jupiter/build/app_specific_files/"
APP_CONFIG_PATH = "/jupiter/build/app_specific_files/app_config.yaml"
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'


def main():
    """ Start polling the profiler home to request the ``scheduling`` file. If succeed, stop the process.
    """
    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)

    FLASK_SVC    = int(config['PORT']['FLASK_SVC'])
    FLASK_DOCKER = int(config['PORT']['FLASK_DOCKER'])
    SELF_IP = os.environ["NODE_IP"]
    HOME_IP = os.environ["HOME_NODE_IP"]

    flag_schedule = "False"
    home_ip = HOME_IP
    while flag_schedule == "False":
        time.sleep(10)
        try:
            log.debug("get the schedule from http://"+ home_ip + ":" + str(FLASK_SVC))
            line = "http://"+home_ip+":" + str(FLASK_SVC) + "/schedule/" + SELF_IP
            r = requests.get(line).json()
            if len(r):
                flag_schedule = r["status"]
        except Exception as e:
            log.debug("Scheduler request failed. Will try again, details: " + str(e))


if __name__ == '__main__':
    main()



