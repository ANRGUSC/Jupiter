__author__ = "Aleksandra Knezevic,Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,  Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import os
import sys
import time
import threading
import json
import configparser
import pyinotify
import queue
import importlib
import logging
# This exists in a build/ folder created by build_push_circe.py
from build.jupiter_utils import app_config_parser
from build.jupiter_utils import transfer

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

"""Paths specific to container (see worker.Dockerfile)"""
APP_DIR = "/jupiter/build/app_specific_files/"
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
CIRCE_INPUT_DIR = '/jupiter/circe_input/'
CIRCE_OUTPUT_DIR = '/jupiter/circe_output/'
sys.path.append(APP_DIR)  # allow imports for app code

# un/pw for all Jupiter subsystem containers
USERNAME = "root"
PASSWORD = "PASSWORD"


class OutputFolderHandler(pyinotify.ProcessEvent):
    def __init__(self, task_name, ssh_port):
        self.task_name = task_name
        self.ssh_port = ssh_port
        super().__init__()

    def process_IN_CLOSE_WRITE(self, event):
        self.handle_output(event)

    def process_IN_MOVED_TO(self, event):
        self.handle_output(event)

    def handle_output(self, event):
        runtime_stat = {
            "event": "new_output_file",
            "filename": event.name,
            "unix_time": time.time(),
        }
        log.info(f"runtime_stat:{json.dumps(runtime_stat)}")
        this_task, dst_task, base_fname = event.name.split("_", maxsplit=3)
        ip = transfer.circe_lookup_ip(dst_task)

        # send output to destination task
        transfer.transfer_data_scp(ip, self.ssh_port, USERNAME, PASSWORD,
                                   event.pathname, CIRCE_INPUT_DIR)


class InputFolderHandler(pyinotify.ProcessEvent):
    def __init__(self, input_q, task_name):
        self.input_q = input_q
        self.task_name = task_name
        super().__init__()

    def process_IN_CLOSE_WRITE(self, event):
        self.handle_input(event)

    def process_IN_MOVED_TO(self, event):
        self.handle_input(event)

    # Gets called when a new input file arrves via SCP from another node
    def handle_input(self, event):
        runtime_stat = {
            "event": "new_input_file",
            "filename": event.name,
            "unix_time": time.time(),
        }
        log.info(f"runtime_stat:{json.dumps(runtime_stat)}")

        # put() just the filename into the queue
        self.input_q.put(event.name)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)
    ssh_svc_port, _ = config['PORT_MAPPINGS']['SSH'].split(':')

    task_name = os.environ['MY_TASK_NAME']
    input_q = queue.Queue()

    app_config = app_config_parser.AppConfig(APP_DIR)
    log.info(f"Using base script {app_config.base_script(task_name)}")
    module_name = app_config.base_script(task_name).replace(".py", "")
    # import task base script from the app_specific_files dir
    task_module = importlib.import_module(
        "build.app_specific_files.{}".format(module_name)
    )

    input_wm = pyinotify.WatchManager()
    input_wm.add_watch(CIRCE_INPUT_DIR, pyinotify.ALL_EVENTS)
    log.debug('starting the input monitoring process')
    input_handler = InputFolderHandler(input_q, task_name)
    in_notifier = pyinotify.ThreadedNotifier(input_wm, input_handler)
    in_notifier.start()

    output_wm = pyinotify.WatchManager()
    output_wm.add_watch(CIRCE_OUTPUT_DIR, pyinotify.ALL_EVENTS)
    log.debug('starting the output monitoring process')
    output_handler = OutputFolderHandler(task_name, ssh_svc_port)
    out_notifier = pyinotify.ThreadedNotifier(output_wm, output_handler)
    out_notifier.start()

    t = threading.Thread(
        target=task_module.task,
        args=(input_q, CIRCE_INPUT_DIR, CIRCE_OUTPUT_DIR, task_name)
    )
    t.start()
    t.join()
