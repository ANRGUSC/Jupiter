import sys
sys.path.append("../../")
import os
import configparser
import jupiter_config
import logging
import random
import paramiko
import socket


logging.basicConfig(level = logging.DEBUG)

# This script must run on XDC to put random stress test on random nodes in order to collect stats from DCOMP testbed 

def get_worker_nodes(node_info_file):
  """read the node info from the file input
  
  Args:
      node_info_file (str): path of ``node.txt``
  
  Returns:
      dict: node information 
  """
  nodes = []
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      if node_line[0].startswith('home'): continue
      nodes.append(node_line[1])
  return nodes

def build_push_stress():
    jupiter_config.set_globals()
    stress_file = 'Dockerfile'
    cmd = "sudo docker build -f %s . -t %s"%(stress_file,jupiter_config.STRESS_IMAGE)
    os.system(cmd)
    os.system("sudo docker push " + jupiter_config.STRESS_IMAGE) 

def gen_random_stress():
    jupiter_config.set_globals()
    num_stress = jupiter_config.NUM_STRESS
    path1 = '../../nodes.txt'
    nodes = get_worker_nodes(path1)
    random_stressed_nodes = random.choices(nodes, k=num_stress)
    return random_stressed_nodes

def run_remote(random_stressed_nodes):
    jupiter_config.set_globals()
    for hostname in random_stressed_nodes:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # no known_hosts error
        myuser = os.getlogin()
        mySSHK = '/home/%s/.ssh/id_rsa.pub'%(myuser)
        ssh.connect(hostname, username=myuser, key_filename=mySSHK)
        cmd_to_execute = "sudo docker pull "+ jupiter_config.STRESS_IMAGE
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute)
        # cmd = "sudo docker run -d --name sim "+ jupiter_config.STRESS_IMAGE
        # os.system(cmd)
        # cmd = "sudo docker exec -it sim python3 /stress_test.py"
        # os.system(cmd)

def prepare_stress_test():
    build_push_stress()
    random_stressed_nodes = gen_random_stress()
    run_remote(random_stressed_nodes)
    
if __name__ == '__main__':
    prepare_stress_test()