__author__ = "Quynh Nguyen, Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "4.0"

import sys
sys.path.append("../")
import time
import jupiter_config
import yaml
import logging
import os
import json

logging.basicConfig(level=logging.DEBUG)

# returns content of yaml in a dictionary
def load_app_config():
    jupiter_config.set_globals()
    app_path = jupiter_config.APP_NAME 
    logging.debug(app_path)
    with open("../../" +app_path + "/app_config.yaml") as f:
        app_config = yaml.load(f, Loader=yaml.FullLoader)
    return app_config

def parse_datasources(app_config):
    sources = app_config['application']['sources']
    datasources = dict()
    for source in sources:
        datasources[source['name']] = dict()
        datasources[source['name']]['dataset']  = source['dataset']
        datasources[source['name']]['datapath'] = source['datapath']
        datasources[source['name']]['stream_image'] = source['stream_image']
    return datasources


if __name__ == '__main__':
    app_config = load_app_config()
    datasources = parse_datasources(app_config)
    logging.debug(datasources.keys())
