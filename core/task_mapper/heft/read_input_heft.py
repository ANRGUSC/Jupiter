"""
   This file read the generated TGFF file as an input of HEFT
"""
__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import os
from pymongo import MongoClient
import threading
import time
import csv
import configparser
import logging

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

"""Paths specific to container (see Dockerfile)"""
JUPITER_CONFIG_INI_PATH = '/jupiter/build/jupiter_config.ini'
HEFT_FILES_DIR = '/jupiter/'


def get_exec_profile_data(exec_home_ip, mongo_svc_port, num_workers):
    """Collect the execution profile from MongoDB in the execution profiler
    home node MongoDB

    Args:
        - exec_home_ip (str): IP of execution profiler home
        - mongo_svc_port (str): Mongo service port
        - num_workers (int): number of worker nodes
    """
    execution_info = []
    num_profilers = 0
    conn = False
    while not conn:
        try:
            client_mongo = MongoClient(
                f'mongodb://{exec_home_ip}:{mongo_svc_port}/'
            )
            db = client_mongo.execution_profiler
            conn = True
        except:
            log.debug('Cannot connect to exec prof home pod, retrying in 60s...')
            time.sleep(60)

    while num_profilers < num_workers:
        try:
            collection = db.collection_names(include_system_collections=False)
            num_profilers = len(collection)
            log.debug('Current number of updated execution profilers: ' +
                      f'{num_profilers}')
            time.sleep(3)
        except Exception:
            log.debug('--- Execution profiler info not yet loaded into ' +
                      'MongoDB! retrying in 60s.')
            time.sleep(60)

    c = 0
    for col in collection:
        log.debug(f'--- Check execution profiler ID : {col}')
        if col == 'home': continue
        logdb = db[col].find()
        for record in logdb:
            # Node ID, Task, Execution Time, Output size
            info_to_csv = [
                col,
                record['Task'],
                record['Duration [sec]'],
                str(record['Output File [Kbit]'])
            ]
            execution_info.append(info_to_csv)
            c += 1
    log.debug('Execution information has already been provided')
    with open(f'{HEFT_FILES_DIR}/execution_log.txt', 'w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(execution_info)


def get_network_data_drupe(
    drupe_worker_ips,
    mongo_svc_port,
    worker_map,
    home_profiler_ip
):
    """Collect the network profile from local MongoDB peer

    Args:
        - drupe_worker_ips (list): IPs of drupe network profilers
        - mongo_svc_port (str): Mongo service port
        - worker_map (dict): mapping of worker IPs to jupiter node name
                             (node1, node2, etc.).
    """
    network_info = []
    for ip in drupe_worker_ips:
        log.debug('Check Network Profiler IP: %s - %s', ip[0], ip[1])
        client_mongo = MongoClient(f'mongodb://{ip[1]}:{mongo_svc_port}/')
        db = client_mongo.droplet_network_profiler
        collection = db.collection_names(include_system_collections=False)
        num_nb = len(collection) - 1
        while num_nb == -1:
            log.debug('--- Network profiler mongoDB not yet prepared')
            time.sleep(60)
            collection = db.collection_names(include_system_collections=False)
            num_nb = len(collection) - 1
        log.debug(f'--- Number of neighbors: {str(num_nb)}')
        num_rows = db[ip[1]].count()
        while num_rows < num_nb:
            log.debug('--- Network profiler regression info not yet loaded ' +
                      'into MongoDB!')
            time.sleep(60)
            num_rows = db[ip[1]].count()

        logdb = db[ip[1]].find().skip(db[ip[1]].count() - num_nb)

        for record in logdb:
            # Source ID, Source IP, Destination ID, Destination IP, Parameters
            if record['Destination[IP]'] in home_profiler_ip:
                continue
            info_to_csv = [
                worker_map[record['Source[IP]']],
                record['Source[IP]'],
                worker_map[record['Destination[IP]']],
                record['Destination[IP]'],
                str(record['Parameters'])
            ]
            network_info.append(info_to_csv)
    log.debug('Network information has already been provided')

    with open(f'{HEFT_FILES_DIR}/network_log.txt', 'w') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(network_info)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(JUPITER_CONFIG_INI_PATH)

    # to contact mongoDB on exec prof and drupe
    mongo_svc_port, _ = config['PORT_MAPPINGS']['MONGO'].split(':')

    # Get all information of profilers (drupe network prof, exec prof)
    drupe_worker_ips = os.environ['DRUPE_WORKER_IPS'].split(' ')
    drupe_worker_ips = [info.split(":") for info in drupe_worker_ips]
    drupe_worker_names = [info[0] for info in drupe_worker_ips]
    drupe_pod_ips = [info[1] for info in drupe_worker_ips]
    worker_map = dict(zip(drupe_pod_ips, drupe_worker_names))
    num_workers = len(drupe_worker_ips)
    drupe_home_ip = os.environ['DRUPE_HOME_IP']
    exec_home_ip = os.environ['EXEC_PROF_HOME_IP']

    threading.Thread(
        target=get_network_data_drupe,
        args=(drupe_worker_ips, mongo_svc_port, worker_map, drupe_home_ip)
    ).start()

    threading.Thread(
        target=get_exec_profile_data,
        args=(exec_home_ip, mongo_svc_port, num_workers)
    ).start()

    while True:
        time.sleep(120)
