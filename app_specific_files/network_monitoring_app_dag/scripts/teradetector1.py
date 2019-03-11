"""
 * Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 * Contributors:
 *    Pranav Sakulkar,
 *    Pradipta Ghosh,
 *    Aleksandra Knezevic,
 *    Jiatong Wang,
 *    Quynh Nguyen,
 *    Jason Tran,
 *    H.V. Krishna Giri Narra,
 *    Zhifeng Lin,
 *    Songze Li,
 *    Ming Yu,
 *    Bhaskar Krishnamachari,
 *    Salman Avestimehr,
 *    Murali Annavaram
 * Read license file in main directory for more details
"""


import os
import time
import json
import paramiko

all_nodes = os.environ["ALL_NODES"].split(":")
all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":")
node_dict = dict(zip(all_nodes, all_nodes_ips))
# print(node_dict)
configs = json.load(open('/centralized_scheduler/config.json'))
tera_idx = configs['taskname_map'][os.environ['TASK']][2]
ssh_port = configs['ssh_port']


      #Keep retrying in case the containers are still building/booting up o 
      #the child nodes.


import os
import time
import json
import paramiko

all_nodes = os.environ["ALL_NODES"].split(":")
all_nodes_ips = os.environ["ALL_NODES_IPS"].split(":")
node_dict = dict(zip(all_nodes, all_nodes_ips))
# print(node_dict)
configs = json.load(open('/centralized_scheduler/config.json'))
tera_idx = configs['taskname_map'][os.environ['TASK']][2]
ssh_port = configs['ssh_port']


      #Keep retrying in case the containers are still building/booting up o 
      #the child nodes.


def task(filename, pathin, pathout):
    retry = 0
    num_retries = 30
    user = "root"
    password = "PASSWORD"
    ssh_port = 5000

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    num = filename.partition('m')[0]

    realMasterIP = node_dict['teramaster' + str(tera_idx)] #"10.244.9.145"

    # send the input file to the real master
    print("Send file")
    while retry < num_retries:
        try:
            ssh.connect(realMasterIP, username=user, password=password, port=ssh_port)
            sftp = ssh.open_sftp()
            sftp.put(pathin + "/"+ filename, "/root/TeraSort/Input/data.txt")
            sftp.close()
            time.sleep(10)
            command = '/root/TeraSort/Master-Detection.sh uncoded'
            ssh.invoke_shell()
            stdin, stdout, stderr = ssh.exec_command(command)
            print(stdout.read())
            break
        except Exception as e:
            print('SSH Connection refused or File transfer failed, will retry in 2 seconds')
            print(e)
            time.sleep(5)
            retry += 1
    ssh.close()
 
    # os.system("sshpass -p 'PASSWORD' scp -o StrictHostKeyChecking=no "
    #           + "-P " + ssh_port + " " +
    #           pathin + "/"+ filename + " root@" +
    #           realMasterIP + ":/root/TeraSort/Input/data.txt")

    

    # Execute uncoded TeraSort
    # For coded TeraSort, replace "uncoded" below by "coded"
    # print("Run code")
    # os.system("sshpass -p 'PASSWORD' ssh -p" + ssh_port + " " +
    #   realMasterIP + " '/root/TeraSort/Master-Detection.sh uncoded'")

    # Download the results
    # For coded TeraSort, replace "result.txt" below by "result-C.txt"
    # print("Download the result")
    # while True:
    #     try:
    #         print("Downlao file")
    #         os.system("sshpass -p 'PASSWORD' scp -o" +
    #                   " StrictHostKeyChecking=no " + "-P " + ssh_port
    #                   + " root@" + realMasterIP +
    #                   ":/root/TeraSort/Output/result.txt " +
    #                   pathout + "/" + str(num) + "anomalies_tera" + str(tera_idx) + ".log")
    #         break
    #     except Exception as e:
    #         print("waiting for output")
    #         time.sleep(1)

    # Remove the results from real master
    # For coded TeraSort, replace "result.txt" below by "result-C.txt"
    print("Download the result and Delete remote files")
    while retry < num_retries:
        try:
            ssh.connect(realMasterIP, username=user, password=password, port=ssh_port)
            time.sleep(10)
            sftp = ssh.open_sftp()
            sftp.get("/root/TeraSort/Output/result.txt", pathout + "/" + str(num) + "anomalies_tera" + str(tera_idx) + ".log")
            sftp.close()
            time.sleep(10)
            command = 'rm /root/TeraSort/Output/result.txt'
            ssh.invoke_shell()
            stdin, stdout, stderr = ssh.exec_command(command)
            print(stdout.read())
            break
        except Exception as e:
            print('Some exception occured')
            print(e)
            time.sleep(5)
            retry += 1
    ssh.close()


    # os.system("sshpass -p 'PASSWORD' ssh -p" + ssh_port + " -o StrictHostKeyChecking=no " + realMasterIP +
    #           " 'rm /root/TeraSort/Output/result.txt'")
    print("Finished")

    fileOut = pathout + "/" + str(num) + "anomalies_tera" + str(tera_idx) + ".log"
    return [fileOut]
def main():

    filelist = '25merged_file1.ipsum'
    outpath = os.path.join(os.path.dirname(__file__), "generated_files/")
    outfile = task(filelist, outpath, outpath)
    return outfile

if __name__ == '__main__':
    oneName = 'data.txt'
    pathin = './'
    pathout = './'
    task(oneName, pathin, pathout)
