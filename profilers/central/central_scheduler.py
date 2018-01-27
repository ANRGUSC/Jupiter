"""
 ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 **     contributor: Quynh Nguyen, Pradipta Ghosh, Bhaskar Krishnamachari
 **     Read license file in main directory for more details
"""
"""
    This is the main script to run in the central network profiler
"""

import pandas as pd
import os
from pymongo import MongoClient
import pandas as pd
import json
from apscheduler.schedulers.background import BackgroundScheduler
import time
import subprocess
import paramiko
from scp import SCPClient
import sys
from os import path
from socket import gethostbyname, gaierror

username     = 'root'   # TODO: Have hardcoded for now. But will change later
password     = 'PASSWORD'
ssh_port     = 5100
num_retries  = 20
retry        = 1

dir_remote   = '/network_profiling/scheduling/'
dir_remote_profiler  =  '/network_profiling/'
source_central_file  = '/network_profiling/central.txt'

"""
    This function updates the estimated quadratic parameters
    in the mongodb server. It checks for any received files 
    from each of the worker droplets in the parameters/ folder.
    If any a file exists, it updates the mongodb.
"""
def do_update_quadratic():
    client_mongo = MongoClient('mongodb://localhost:27017/')
    db = client_mongo.central_network_profiler
    parameters_folder = os.path.join(os.getcwd(),'parameters')
    logging = db['quadratic_parameters']
    try:
        for subdir, dirs, files in os.walk(parameters_folder):
            for file in files:
                if file.startswith("."): 
                    continue
                
                print(file)
                measurement_file = os.path.join(subdir, file)
                df = pd.read_csv(measurement_file, delimiter = ',', header = 0)
                data_json = json.loads(df.to_json(orient = 'records'))
                logging.insert(data_json)
    except Exception as e:
        print(e)




if __name__ == '__main__':

    nodes_info = 'central_input/nodes.txt'
    df_nodes   = pd.read_csv(nodes_info, header = 0, delimiter = ',',index_col = 0)
    node_list  = df_nodes.T.to_dict('list')

    # load the list of links from the csv file
    links_info = 'central_input/link_list.txt'
    df_links   = pd.read_csv(links_info, header = 0)
    df_links.replace('(^\s+|\s+$)', '', regex = True, inplace = True)

    # check the folder for putting output files
    scheduling_folder = 'scheduling'
    output_file = 'scheduling.txt'
    if not os.path.exists(scheduling_folder):
        os.makedirs(scheduling_folder)

    # write central profiler info where each node should send their data
    with open(source_central_file, 'w') as f:
        line = os.environ['SELF_IP']+ " " + username + " " + password
        f.write(line)
    
    print('Step 1: Create the central database ')
    client_mongo = MongoClient('mongodb://localhost:27017/')
    db = client_mongo['central_network_profiler']
    buffer_size = len(df_links.index) * 100
    db.create_collection('quadratic_parameters', capped = True,
                                 size = 100000, max = buffer_size)

    print('Step 2: Preparing the scheduling text files')
    for cur_node, row in df_nodes.iterrows():
        # create separate scheduling folders for separate nodes
        cur_schedule = os.path.join(scheduling_folder, node_list.get(cur_node)[0])
        if not os.path.exists(cur_schedule):
            os.makedirs(cur_schedule)

        outgoing_links_info = df_links.loc[df_links['Source'] == cur_node]
        outgoing_links_info = pd.merge(outgoing_links_info, df_nodes, left_on = 'Destination', right_index = True, how = 'inner')

        # prepare the output schedule. it has two clumns Node and Region (location)
        schedule_info = pd.DataFrame(columns = ['Node','Region'])
        # Append the self ip address and the self region
        schedule_info = schedule_info.append({'Node':node_list.get(cur_node)[0],
                                    'Region':row['Region']}, ignore_index = True)
        # append all destination address and their region
        schedule_info = schedule_info.append(outgoing_links_info[['Node','Region']], ignore_index = False)
        # write the schedule to the output csv file

        scheduler_file = os.path.join(cur_schedule, output_file)
        schedule_info.to_csv(scheduler_file, header = False, index = False)
        
        print('Step 3: Copying files and network scripts to the droplets ')

        """
            Create a ssh connection to the respective droplet and transfer
            the scheduler.txt and central.txt file to proper folders in order
            to trigger the profiling
        """
        if path.isfile(scheduler_file) and path.isfile(source_central_file):
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            while retry < num_retries:
                try:
                    client.connect(node_list.get(cur_node)[0],
                            username = username, password = password,
                            port = ssh_port)
                    scp = SCPClient(client.get_transport())
                    scp.put(scheduler_file, dir_remote)
                    scp.put(source_central_file, dir_remote_profiler)
                    scp.close() 
                    print('File transfer complete to ' + cur_node + '\n')
                    break
                except (paramiko.ssh_exception.NoValidConnectionsError, gaierror):
                    print('SSH Connection refused, will retry in 2 seconds')
                    time.sleep(2)
                    retry += 1
        else:
            print('No such file exists...')



    print('Step 4: Scheduling updating the central database')
    # create the folder for each droplet/node to report the local data to
    parameters_folder = 'parameters'
    if not os.path.exists(parameters_folder):
        os.makedirs(parameters_folder)

    # create a background job to update the mongodb with the received parameters
    sched = BackgroundScheduler()
    sched.add_job(do_update_quadratic,'interval', id = 'update',
                               minutes = 10,replace_existing = True)
    sched.start()
    while True:
        print('waiting for update...')
        time.sleep(60)
    #sched.shutdown()

