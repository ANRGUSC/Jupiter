"""
   This file implements HEFT code in the kubernettes system.
"""
__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import heft_dup
import os
import time
from flask import Flask
import json
import configparser
import logging
# This exists in a build/ folder created by build_push_mapper.py
from build.jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

"""Paths specific to container (see Dockerfile)"""
TGFF_FILE = "/jupiter/input.tgff"
APP_DIR = "/jupiter/build/app_specific_files/"
JUPITER_CONFIG_INI_PATH = "/jupiter/build/jupiter_config.ini"

app = Flask(__name__)
task_mapping = {}
num_tasks = -1


def return_task_mapping():
    """Respond with the task mapping only when it's finished. Otherwise,
    respond with an empty dict.

    Returns:
        json: task mapping of tasks and corresponding nodes
    """
    if num_tasks < 0:
        log.error("invalid number of tasks")

    log.info("Recieved request for task mapping. Current mappings done: " +
             f"{len(task_mapping)}")
    log.info("task mapping: " + json.dumps(task_mapping, indent=4))
    if len(task_mapping) == num_tasks:
        return json.dumps(task_mapping)
    else:
        log.info('task_mapping not yet finished, responding with empty dict()')
        return json.dumps(dict())


app.add_url_rule('/', 'return_task_mapping', return_task_mapping)


if __name__ == '__main__':
    app_config = app_config_parser.AppConfig(APP_DIR)
    task_names = app_config.get_task_names()
    num_tasks = len(task_names)

    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)

    log.info('Starting to run HEFT task mapping')
    starting_time = time.time()

    worker_names = os.environ["WORKER_NODE_NAMES"].split(':')
    _, flask_port = config['PORT_MAPPINGS']['FLASK'].split(':')

    output = "/jupiter/input_to_CIRCE.txt"
    while True:
        if os.path.isfile(TGFF_FILE):
            log.info('File TGFF was generated!!!')
            heft_scheduler = heft_dup.HEFT(TGFF_FILE, worker_names)
            heft_scheduler.run(task_mapper="heft")
            heft_scheduler.output_file(output)
            log.info(f'HEFT output file: {output}')
            task_mapping = heft_scheduler.output_assignments()
            log.info('Assigning random master and slaves')
            heft_scheduler.display_result()
            t = time.time()

            if len(task_mapping) == num_tasks:
                log.debug('Successfully finished HEFT task_mapping')
                end_time = time.time()
                deploy_time = end_time - starting_time
                log.debug(f'Time to finish HEFT task mapping {deploy_time}')

            break
        else:
            log.debug('TGFF file not yet generated, retrying in 5s...')
            time.sleep(5)

    app.run(host='0.0.0.0', port=int(flask_port))
