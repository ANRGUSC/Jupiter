__author__ = "Pradipta Ghosh, Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import os
from os import path
import json
import time
import requests
import pyinotify
from pymongo import MongoClient
import pandas as pd
import datetime
import shutil
import configparser
import logging
import importlib
# This exists in a build/ folder created by build_push_exec.py
from build.jupiter_utils import app_config_parser
import utils
import sys


logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

"""Paths specific to container (see home.Dockerfile)"""
APP_DIR = "/jupiter/build/app_specific_files/"
sys.path.append(APP_DIR)
APP_CONFIG_PATH = "/jupiter/build/app_specific_files/app_config.yaml"
PROFILER_FILES_DIR = '/jupiter/exec_profiler/profiler_files/'
PROFILER_FILES_PROCESSED_DIR = '/jupiter/exec_profiler/profiler_files_processed/'
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
sys.path.append(APP_DIR)
# un/pw for all execution profiler containers
USERNAME = "root"
PASSWORD = "PASSWORD"


class MyEventHandler(pyinotify.ProcessEvent):

    """Handling the event when new execution profiler files are generated
    """

    def process_IN_CLOSE_WRITE(self, event):
        """Write execution profiling information into local MongoDB database

        Args:
            event (str): New execution profiler files created
        """
        log.debug("New execution profiler files created: {}"
                      .format(event.pathname))
        file_name = os.path.basename(event.pathname)
        node_info = file_name.split('_')[1]
        node_info = node_info.split('.')[0]
        log.debug("Node info: %s", node_info)
        client_mongo = MongoClient(
            'mongodb://localhost:' + str(MONGO_PORT) + '/'
        )
        db = client_mongo['execution_profiler']
        db.create_collection(node_info)
        logdb = db[node_info]

        try:
            df = pd.read_csv(
                event.pathname,
                delimiter=',',
                header=0,
                names=["Task", "Duration [sec]", "Output File [Kbit]"]
            )
            data_json = json.loads(df.to_json(orient='records'))
            logdb.insert(data_json)
            log.debug('MongodB Update Successful')
        except Exception as e:
            log.debug('MongoDB error')
            log.debug(e)


def update_mongo(file_path):
    """Update the MongoDb with the data from the Execution profiler

    Args:
        file_path (str): The file path
    """
    file_name = os.path.basename(file_path)
    node_info = file_name.split('_')[1]
    node_info = node_info.split('.')[0]
    log.debug("Node info: %s", node_info)
    client_mongo = MongoClient('mongodb://localhost:' + str(MONGO_PORT) + '/')
    db = client_mongo['execution_profiler']
    db.create_collection(node_info)
    logdb = db[node_info]
    try:
        df = pd.read_csv(file_path, delimiter=',', header=0,
                         names=["Task","Duration [sec]", "Output File [Kbit]"])
        data_json = json.loads(df.to_json(orient='records'))
        logdb.insert(data_json)
        log.debug('MongodB Update Successful')
    except Exception as e:
        log.debug('MongoDB error')
        log.debug(e)


def main():
    """
        -   Load all the confuguration
        -   create the task list in the order of execution
        -   execute each task and get the timing and data size
        -   send intermediate files to the worker execution profilers
        -   Transfer the Intermdiate Files To all the Workers.
        -   Start Waiting For Incoming Statistics from the Worker Execution
            Profilers. Once a File arrives at the ``PROFILER_FILES_DIR``
            immediately process it and move it to the
            ``PROFILER_FILES_PROCESSED_DIR`` to keep track of processed files
    """
    # Load all the confuguration
    log.debug('Starting to run execution profiler')
    starting_time = time.time()
    nodename = os.environ['NODE_NAME']

    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)

    global EXC_FPORT, MONGO_PORT

    EXC_FPORT = int(config['PORT']['FLASK_SVC'])
    MONGO_PORT = int(config['PORT']['MONGO_DOCKER'])

    log.info("nodename: {}".format(nodename))

    myfile = open('/jupiter/profiler_' + nodename + '.txt', "w")
    myfile.write('task,time(sec),output_data (Kbit)\n')

    app_config = app_config_parser.AppConfig(APP_DIR, "don't care")
    task_list = app_config.get_dag_tasks()

    #execute each task and get the timing and data size
    for task in task_list:
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
        line = task['name'] + ',' + str(mytime) + ',' + str(sum_output_data) \
               + '\n'
        myfile.write(line)
        myfile.flush()

    myfile.close()

    log.info('profiler_home: finished task profiling')

    # hack: set nodes that sources are to be scheduled on as having high
    # execution times so HEFT does not schedule anything on them
    sources = app_config.get_source_names()
    log.debug(sources)
    for src in sources:
        src_path = "/jupiter/profiler_" + src + ".txt"
        myfile = open(src_path, "w")
        myfile.write('task,time(sec),output_data (Kbit)\n')

        big_number = '100000000000000'
        for task in task_list:
            mytime = int(big_number)
            sum_output_data = int(big_number)
            line = task['name'] + ',' + str(mytime) + ',' + str(sum_output_data) + '\n'
            myfile.write(line)
            myfile.flush()
        myfile.close()

        update_mongo(src_path)
        processed_file = PROFILER_FILES_PROCESSED_DIR + "profiler_" + src + '.txt'
        shutil.move(src_path, processed_file)

    log.debug('profiler_home: Sending output files back to the master node...')

    # TODO: send the intermedaiate files to the remote location
    # TODO: send a signal to the k8 to remove the nonDAG tasks

    # send intermediate files to the worker execution profilers
    log.debug('Copy supertask information to /jupiter/profilers_files directory')
    master_profile_path = "/jupiter/profiler_" + nodename + '.txt'
    if path.isfile(master_profile_path):
        shutil.move(master_profile_path, PROFILER_FILES_DIR)
    else:
        log.error("{} missing!".format(master_profile_path))

    # env vars injected via kubernetes induring k8s_exec_scheduler.py
    profilers_ips = os.environ['ALL_PROFILER_IPS'].split(':')
    allprofiler_names = os.environ['ALL_PROFILER_NAMES'].split(':')
    profilers_ip_map = dict(zip(allprofiler_names, profilers_ips))

    for node in allprofiler_names:
        log.debug('----------------------------------')
        try:
            log.debug("start the profiler in %s", node)
            log.debug(profilers_ip_map[node])
            # this get request executes profiler_worker.py remotely
            requests.get("http://" + profilers_ip_map[node] + ":"
                         + str(EXC_FPORT))
        except Exception as e:
            log.debug("Exception in sending data")
            log.debug(e)

    # Now we wait for incoming exec profiler statistics from all other nodes
    # Once a file arrives at the PROFILER_FILES_DIR immediately process it and
    # move it to PROFILER_FILES_PROCESSED_DIR to keep track of processed files
    log.debug('Watching the incoming execution profiler files...')

    # expecting to receive as many files as there are nodes in the k8s cluster
    num_files = app_config.get_num_nodes()
    received = 0
    while received < num_files:
        directory = os.listdir(PROFILER_FILES_DIR)
        for file in directory:
            try:
                log.debug('--- Add execution info from file: ' + file)
                src_path = PROFILER_FILES_DIR + '/' + file
                update_mongo(src_path)
                shutil.move(src_path, PROFILER_FILES_PROCESSED_DIR + file)
                received += 1
            except Exception as e:
                log.debug("profiler_home: Some Exception")
                log.debug(e)

        log.debug("Update: %s node has reported execution profiling stats",
                  str(received))
        if received == num_files:
            log.debug('Successfully finish execution profiler!')
            end_time = time.time()
            total_time = end_time - starting_time
            log.debug('Time to finish execution profiler: %s',
                          str(total_time))
            break
        time.sleep(60)

    while 1:
        log.debug("Execution profiler finished. %s files received.",
                      str(received))
        time.sleep(60)


if __name__ == '__main__':
    main()
