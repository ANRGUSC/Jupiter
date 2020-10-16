__author__ = "Pradipta Ghosh, Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
import sys
import datetime
import configparser
import logging
import utils
# This exists in a build/ folder created by build_push_exec.py
from build.jupiter_utils import app_config_parser
from build.jupiter_utils import transfer
import importlib

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# paths specific to container (see worker.Dockerfile)
APP_DIR = "/jupiter/build/app_specific_files/"
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
PROFILER_FILES_DIR = "/jupiter/exec_profiler/profiler_files/"
HOME_PROFILER_FILES_DIR = PROFILER_FILES_DIR
sys.path.append(APP_DIR)  # allow imports for app code

# un/pw for all execution profiler containers
USERNAME = "root"
PASSWORD = "PASSWORD"


def main():
    """
        -   Load all the confuguration
        -   create the task list in the order of execution
        -   execute each task and get the timing and data size
        -   send output file back to the scheduler machine
    """
    # Load all the confuguration
    log.debug('Load all the configuration')
    nodename = os.environ['NODE_NAME']
    log.debug("nodename: {}".format(nodename))

    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)

    myfile = open('/jupiter/profiler_' + nodename + '.txt', "w")
    myfile.write('task,time(sec),output_data (Kbit)\n')

    app_config = app_config_parser.AppConfig(APP_DIR)
    tasks = app_config.get_dag_tasks()

    #execute each task and get the timing and data size
    for task in tasks:
        module_name = task['base_script'].replace(".py", "")
        # import task base script from the app_specific_files dir
        task_module = importlib.import_module(
            "build.app_specific_files.{}".format(module_name)
        )

        start_time = datetime.datetime.utcnow()
        output_dir, output_files = task_module.profile_execution(task['name'])
        log.debug('------------------------------------------------')
        log.debug(output_files)
        stop_time = datetime.datetime.utcnow()
        mytime = stop_time - start_time
        mytime = int(mytime.total_seconds())  # convert to seconds (rounds)

        output_sizes = []
        for file in output_files:
            output_sizes.append(
                utils.file_size(os.path.join(output_dir, file))
            )
        log.debug(output_sizes)
        log.debug('------------------------------------------------')
        sum_output_data = sum(output_sizes)  # current: sum of all output files
        line = task['name'] + ',' + str(mytime) + ',' + str(sum_output_data) + '\n'
        myfile.write(line)
        myfile.flush()

    myfile.close()

    log.debug('Finish logging.debuging out the execution information')
    log.debug('Starting to send the output file back to the home node')

    # send output file back to the "home" node
    home_ip = os.environ['HOME_NODE_IP']
    service, docker = config['PORT_MAPPINGS']['SSH'].split(':')
    ssh_port = service

    local_profiler_path = '/jupiter/profiler_' + nodename + '.txt'

    if os.path.isfile(local_profiler_path):
        transfer.transfer_data_scp(home_ip, ssh_port, USERNAME, PASSWORD,
                                        local_profiler_path,
                                        HOME_PROFILER_FILES_DIR)
    else:
        log.debug('No Runtime data file exists...')


if __name__ == '__main__':
    main()
