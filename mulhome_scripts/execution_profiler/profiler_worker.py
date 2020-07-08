__author__ = "Pradipta Ghosh, Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
from os import path
import datetime
import configparser
import logging
import exec_profiler
import jupiter_utils
import importlib

logging.basicConfig(level=logging.DEBUG)

# paths specific to container (see exec_profiler_worker.Dockerfile)
APP_CONFIG_PATH = '/jupiter/app_specific_files/app_config.yaml'
JUPITER_CONFIG_INI_PATH = '/jupiter/jupiter_config.ini'
PROFILER_FILES_DIR = "/jupiter/exec_profiler/profiler_files/"
HOME_PROFILER_FILES_DIR = PROFILER_FILES_DIR

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
    logging.debug('Load all the configuration')
    nodename = os.environ['NODE_NAME']

    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)

    BOKEH_SERVER = config['BOKEH_LIST']['BOKEH_SERVER']
    BOKEH_PORT = int(config['BOKEH_LIST']['BOKEH_PORT'])
    BOKEH = int(config['BOKEH_LIST']['BOKEH'])

    logging.debug("nodename: {}".format(nodename))

    myfile = open('/jupiter/profiler_' + nodename + '.txt', "w")
    myfile.write('task,time(sec),output_data (Kbit)\n')

    task_list = jupiter_utils.get_tasks(APP_CONFIG_PATH)

    #execute each task and get the timing and data size
    for task in task_list:
        # import each task file from the app_specific_files dir
        task_module = importlib.import_module(
            "app_specific_files.scripts.{}".format(task)
        )

        start_time = datetime.datetime.utcnow()
        output_dir, output_file_names = task_module.profile_execution()
        logging.debug('------------------------------------------------')
        logging.debug(output_file_names)
        stop_time = datetime.datetime.utcnow()
        mytime = stop_time - start_time
        mytime = int(mytime.total_seconds())  # convert to seconds

        output_sizes = []
        for file in output_file_names:
            output_sizes.append(
                exec_profiler.file_size(os.path.join(output_dir, file))
            )
        logging.debug(output_sizes)
        logging.debug('------------------------------------------------')
        sum_output_data = sum(output_sizes)  # current: sum of all output files
        line = task + ',' + str(mytime) + ',' + str(sum_output_data) + '\n'
        myfile.write(line)
        myfile.flush()

    myfile.close()

    logging.debug('Finish logging.debuging out the execution information')
    logging.debug('Starting to send the output file back to the master node')

    # send output file back to the "home" node
    home_ip = os.environ['HOME_NODE']
    ssh_port = int(config['PORT']['SSH_SVC'])

    local_profiler_path = '/jupiter/profiler_' + nodename + '.txt'

    if path.isfile(local_profiler_path):
        jupiter_utils.transfer_data_scp(home_ip, ssh_port, USERNAME, PASSWORD,
                                        local_profiler_path,
                                        HOME_PROFILER_FILES_DIR)
        if BOKEH == 3:
            topic = "msgoverhead_%s" % (nodename)
            msg = 'msgoverhead executionprofiler sendexecinfo %d\n' % (len(tasks))
            exec_profiler.demo_help(BOKEH_SERVER, BOKEH_PORT, topic, msg)
    else:
        logging.debug('No Runtime data file exists...')


if __name__ == '__main__':
    main()
