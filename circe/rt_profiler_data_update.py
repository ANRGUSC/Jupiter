#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Aleksandra Knezevic,Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar, Jason A Tran and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.0"
 
import paramiko
from scp import SCPClient
import os
import sys
from os import path
from socket import gethostbyname, gaierror
import time
import configparser

def main():
    """
    This script apparently needs to run every kth minute to send the local runtime information to the central scheduler node.
    The runtime recording is actually embedded in the ``task#.py``.
    
        - ``runtime/droplet_runtime_input_+ node_name`` stores the start time of the job for an incoming data
        - ``runtime/droplet_runtime_output_+ node_name`` stores the end time of job processing.
    """

    #  Load all the confuguration
    INI_PATH = '/jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)

    scheduler_IP = os.environ['HOME_NODE'] 
    username     = config['AUTH']['USERNAME']
    password     = config['AUTH']['PASSWORD']
    ssh_port     = int(config['PORT']['SSH_SVC'])
    num_retries  = int(config['OTHER']['SSH_RETRY_NUM'])
    retry        = 1

    dir_remote        = '/runtime'
    node_name         = os.environ['NODE_NAME']
    local_input_path  = '/centralized_scheduler/runtime/droplet_runtime_input_' + node_name
    local_output_path = '/centralized_scheduler/runtime/droplet_runtime_output_' + node_name

    """
        Check if the files exists. 
    """
    while True:
        if path.isfile(local_input_path) and path.isfile(local_output_path):
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            remote_path = dir_remote
            while retry < num_retries:
                try:
                    client.connect(scheduler_IP, username=username, password=password, port=ssh_port)
                    scp = SCPClient(client.get_transport())
                    scp.put(local_input_path, remote_path)
                    scp.put(local_output_path, remote_path)
                    scp.close() 
                    os.remove(local_input_path)
                    os.remove(local_output_path)
                    print('Runtime data transfer complete\n')
                    break
                except:
                    print('SSH Connection refused or Some Connection Error, will retry in 2 seconds')
                    time.sleep(2)
                    retry += 1
        else:
            print('No Runtime data file exists...')

        time.sleep(300)


if __name__ == '__main__':
    main()

