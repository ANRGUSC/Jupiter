"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pradipta Ghosh
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""


import multiprocessing
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import sys
import time
import json
import paramiko
import datetime
from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
import netifaces as ni
import platform
from os import path
from socket import gethostbyname, gaierror, error
import multiprocessing
import time
import urllib.request
from urllib import parse

configs = json.load(open('/centralized_scheduler/config.json'))
taskmap = configs["taskname_map"][sys.argv[len(sys.argv)-1]]
print(taskmap)
taskname = taskmap[0]
print(taskname)
if taskmap[1] == True:
    taskmodule = __import__(taskname)

#target port for SSHing into a container
ssh_port = 5000
filenames=[]
files_out=[]
node_name = os.environ['NODE_NAME']
home_node_host_port = os.environ['HOME_NODE'] + ":48888"

all_nodes = os.environ["ALL_NODES"].split(":")
all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":")

def send_monitor_data(msg):
    try:
        print("Sending message", msg)
        url = "http://" + home_node_host_port + "/recv_monitor_data"
        params = {'msg': msg, "work_node": taskname}
        params = parse.urlencode(params)
        req = urllib.request.Request(url='%s%s%s' % (url, '?', params))
        res = urllib.request.urlopen(req)
        res = res.read()
        res = res.decode('utf-8')
    except Exception as e:
        print("Sending message to flask server on home FAILED!!!")
        print(e)
        return "not ok"
    return res


#for OUTPUT folder 
class Watcher1():
    
    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'output/')

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.observer = Observer()

    def run(self):
        event_handler = Handler1()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()

class Handler1(FileSystemEventHandler):


    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
             
            print("Received file as output - %s." % event.src_path)

            #Runtime profiler (finished_time)
            
            """
                Save the time when a output file is available. This is taken as the end time of the task.
                The output time is stored in the file central_scheduler/runtime/droplet_runtime_output_(%node name)
            """
            execution_end_time = datetime.datetime.utcnow()
            pathrun = '/centralized_scheduler/runtime/'
            runtime_file = os.path.join(pathrun,'droplet_runtime_output_' + node_name)
            new_file = os.path.split(event.src_path)[-1]

            if '_' in new_file:
                temp_name = new_file.split('_')[0]
            else:
                temp_name = new_file.split('.')[0]
            with open(runtime_file, 'a') as f:
                line = 'created_output, %s, %s, %s, %s\n' % (node_name, taskname, temp_name, execution_end_time)
                f.write(line)
            

            global files_out

            #based on flag2 decide whether to send one output to all children or different outputs to different children in
            #order given in the config file
            flag2 = sys.argv[2]

            #if you are sending the final output back to scheduler
            if sys.argv[3] == 'home':
                
                IPaddr = sys.argv[4]
                user = sys.argv[5]
                password=sys.argv[6]
                #port=int(sys.argv[7])
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                #Keep retrying in case the containers are still building/booting up on
                #the child nodes.
                retry = 0
                num_retries = 30
                while retry < num_retries:
                    try:
                        ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                        break
                    except (paramiko.ssh_exception.NoValidConnectionsError, gaierror):
                        print('SSH Connection refused, will retry in 2 seconds')
                        time.sleep(2)
                        retry += 1

                sftp = ssh.open_sftp()
                sftp.put(event.src_path, os.path.join('/output', new_file))
                sftp.close()
                ssh.close()

            elif flag2 == 'true':

                for i in range(3, len(sys.argv)-1,4):
                    IPaddr=sys.argv[i+1]
                    user=sys.argv[i+2]
                    password=sys.argv[i+3]
                    #port = int(sys.argv[i+4])

                    ssh=paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    #Keep retrying in case the containers are still building/booting up on
                    #the child nodes.
                    retry = 0
                    num_retries = 30
                    while retry < num_retries:
                        try:
                            ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                            break
                        except (paramiko.ssh_exception.NoValidConnectionsError, gaierror):
                            print('SSH Connection refused, will retry in 2 seconds')
                            time.sleep(2)
                            retry += 1

                    sftp = ssh.open_sftp()
                    sftp.put(event.src_path, os.path.join('/centralized_scheduler', 'input', new_file))
                    sftp.close()
                    ssh.close()

            else:
                num_child = (len(sys.argv) - 4) / 4
                files_out.append(new_file)

                if (len(files_out) == num_child):

                        
                    for i in range(3, len(sys.argv)-1,4):
                        myfile = files_out.pop(0)
                        event_path = os.path.join(''.join(os.path.split(event.src_path)[:-1]), myfile)
                        IPaddr=sys.argv[i+1]
                        user=sys.argv[i+2]
                        password=sys.argv[i+3]
                        #port = int(sys.argv[i+4])

                        ssh=paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                        #Keep retrying in case the containers are still building/booting up on
                        #the child nodes.
                        retry = 0
                        num_retries = 30
                        while retry < num_retries:
                            try:
                                ssh.connect(IPaddr, username=user, password=password, port=ssh_port)
                                break
                            except (paramiko.ssh_exception.NoValidConnectionsError, gaierror):
                                print('SSH Connection refused, will retry in 2 seconds')
                                time.sleep(2)
                                retry += 1
                
                        sftp = ssh.open_sftp()
                        sftp.put(event_path, os.path.join('/centralized_scheduler','input', myfile))
                        sftp.close()
                        ssh.close()

                    files_out=[]


#for INPUT folder
class Watcher(multiprocessing.Process):

    DIRECTORY_TO_WATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),'input/')
    
    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()

class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':

            print("Received file as input - %s." % event.src_path)
            new_file = os.path.split(event.src_path)[-1]

            #Runtime profiler (created_time)
            
            if platform.system() == 'Windows':
                print(os.path.getctime(event.src_path))
            else:
                print(event.src_path)
                stat = os.stat(event.src_path)
                try:
                    print(stat.st_birthtime)
                except AttributeError:
                    created_time=datetime.datetime.fromtimestamp(stat.st_mtime)
                    print(created_time)

            """
                Save the time when an input file is available. This is taken as the start time of the task.
                The output time is stored in the file central_scheduler/runtime/droplet_runtime_input_(%node name)
            """
            execution_start_time = datetime.datetime.utcnow()
            pathrun = '/centralized_scheduler/runtime/'
            runtime_file = os.path.join(pathrun,'droplet_runtime_input_' + node_name)
            new_file = os.path.split(event.src_path)[-1]
            if '_' in new_file:
                temp_name = new_file.split('_')[0]
            else:
                temp_name = new_file.split('.')[0]

            with open(runtime_file, 'a') as f:
                line = 'created_input, %s, %s, %s, %s\n' %(node_name, taskname, temp_name, execution_start_time)
                f.write(line)

            q.put(new_file)
            filename = new_file
            

            global filenames
            flag1 = sys.argv[1]

            if flag1 == "1":
                # Start msg
                send_monitor_data("start")
                inputfile=q.get()
                input_path = os.path.split(event.src_path)[0]
                output_path = os.path.join(os.path.split(input_path)[0],'output')
                dag_task = multiprocessing.Process(target=taskmodule.task, args=(inputfile, input_path, output_path))
                dag_task.start()
                dag_task.join()
                send_monitor_data("end")
                # end msg
            else:

                filenames.append(q.get())
                if (len(filenames) == int(flag1)):
                    #start msg
                    send_monitor_data("start")
                    input_path = os.path.split(event.src_path)[0]
                    output_path = os.path.join(os.path.split(input_path)[0],'output')

                    dag_task = multiprocessing.Process(target=taskmodule.task, args=(filenames, input_path, output_path))
                    dag_task.start()
                    dag_task.join()
                    filenames = []
                    send_monitor_data("end")
                    # end msg

if __name__ == '__main__':

    if taskmap[1] == True:
        q=multiprocessing.Queue()

        #monitor INPUT as another process
        w=Watcher()
        w.start()

        #monitor OUTPUT in this process
        w1=Watcher1()
        w1.run()
    else:

        print(taskmap[2:])
        path_src = "/centralized_scheduler/" + taskname
        args = ' '.join(str(x) for x in taskmap[2:])

        if os.path.isfile(path_src + ".py"):
            cmd = "python3 -u " + path_src + ".py " + args          
        else:
            cmd = "sh " + path_src + ".sh " + args
        print(cmd)
        os.system(cmd)
