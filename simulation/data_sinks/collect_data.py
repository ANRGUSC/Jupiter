__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"
"""
    Streaming data generator
"""
import time
import os
import subprocess
import pyinotify
import paramiko
from scp import SCPClient
import _thread
from multiprocessing import Process
import multiprocessing
from flask import Flask, request
import configparser
import urllib
import logging

logging.basicConfig(level = logging.DEBUG)

app = Flask(__name__)

end_times = dict()

class Handler(pyinotify.ProcessEvent):
    """Setup the event handler for all the events
    """


    def process_IN_CLOSE_WRITE(self, event):
        """On every node, whenever there is scheduling information sent from the central network profiler:
            - Connect the database
            - Scheduling measurement procedure
            - Scheduling regression procedure
            - Start the schedulers
        
        Args:
            event (ProcessEvent): a new file is created
        """

        logging.debug("Received file as input at the datasink - %s." % event.pathname)  


        inputfile = event.pathname.split('/')[-1]
        t = time.time()
        end_times[inputfile] = t
        new_file_name = os.path.split(event.pathname)[-1]

        send_monitor_data(inputfile,'output',t)

class MonitorRecv(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        """
        Start Flask server
        """
        logging.debug("Flask server started")
        app.run(host='0.0.0.0', port=FLASK_DOCKER)


def send_monitor_data(filename,filetype,ts):
    """
    Sending message to flask server on home

    Args:
        msg (str): the message to be sent

    Returns:
        str: the message if successful, "not ok" otherwise.

    Raises:
        Exception: if sending message to flask server on home is failed
    """
    try:
        url = "http://" + home_node_host_port + "/recv_monitor_datasink"
        params = {'filename': filename, "filetype": filetype,"time":ts}
        params = urllib.parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        logging.debug("Sending message to flask server on home FAILED!!!")
        logging.debug(e)
        return "not ok"
    return res

def main():
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    global FLASK_SVC,FLASK_DOCKER,username, password, TRANSFER,num_retries,ssh_port
    FLASK_DOCKER   = int(config['PORT']['FLASK_DOCKER'])
    username    = config['AUTH']['USERNAME']
    password    = config['AUTH']['PASSWORD']
    TRANSFER = int(config['CONFIG']['TRANSFER'])
    num_retries = int(config['OTHER']['SSH_RETRY_NUM'])
    ssh_port    = int(config['PORT']['SSH_SVC'])
    FLASK_SVC   = int(config['PORT']['FLASK_SVC'])


    global home_node_host_port
    home_node_host_port = os.environ['HOME_NODE'] + ":" + str(FLASK_SVC)


    web_server = MonitorRecv()
    web_server.start()

    # watch manager
    wm = pyinotify.WatchManager()
    input_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'/centralized_scheduler/input/')
    wm.add_watch(input_folder, pyinotify.ALL_EVENTS, rec=True)
    logging.debug('starting the input monitoring process\n')
    eh = Handler()
    notifier = pyinotify.Notifier(wm, eh)
    notifier.loop()

 

if __name__ == '__main__':
    main()    
