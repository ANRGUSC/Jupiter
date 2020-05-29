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
def load_app_config(app_config_path):
    with open(app_config_path) as f:
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
        datasources[source['name']]['node_placement'] = source['node_placement']
    return datasources


if __name__ == '__main__':
    # jupiter_config.set_globals()
    # app_path = jupiter_config.APP_NAME 
    # logging.debug(app_path)
    # app_config_path = "../" +app_path + "/app_config.yaml"
    app_config_path = '../tools/duplicate/demotest/app_config.yaml'
    app_config = load_app_config(app_config_path)
    datasources = parse_datasources(app_config)
    tmp =[]
    for name in datasources:
        tmp.append(datasources[name]['dataset'])
    logging.debug(tmp)