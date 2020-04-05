import sys
sys.path.append("../../")
import os
import configparser
import jupiter_config
import logging
import random
import paramiko
import socket


logging.basicConfig(level = logging.INFO)

# This script must run on XDC to put random stress test on random nodes in order to collect stats from DCOMP testbed 

def get_nodes(node_info_file):
  """read the node info from the file input
  
  Args:
      node_info_file (str): path of ``node.txt``
  
  Returns:
      dict: node information 
  """
  nodes = []
  homes = []
  node_file = open(node_info_file, "r")
  for line in node_file:
      node_line = line.strip().split(" ")
      if node_line[0].startswith('home'): 
        homes.append(node_line[1])
      else:
        nodes.append(node_line[1])
  return homes, nodes

def build_push_stress():
    jupiter_config.set_globals()
    print(jupiter_config.STRESS_IMAGE)
    # Master node on DCOMP n0
    ssh = connect_remote_ssh('n0')
    cmd_to_execute = '(cd Jupiter/simulation/stress_test/; sudo docker build -f Dockerfile . -t %s)'%(jupiter_config.STRESS_IMAGE)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute, get_pty=True)
    for line in ssh_stdout:
        print(line)
    cmd_to_execute = "sudo docker push " + jupiter_config.STRESS_IMAGE
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute, get_pty=True)
    for line in ssh_stdout:
        print(line)

def gen_random_stress(nodes):
    jupiter_config.set_globals()
    num_stress = jupiter_config.NUM_STRESS
    random_stressed_nodes = random.choices(nodes, k=num_stress)
    return random_stressed_nodes

def connect_remote_ssh(hostname):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # no known_hosts error
    myuser = os.getlogin()
    mySSHK = '/home/%s/.ssh/id_rsa.pub'%(myuser)
    ssh.connect(hostname, username=myuser, key_filename=mySSHK)
    return ssh

def run_remote(random_stressed_nodes):
    jupiter_config.set_globals()
    for hostname in random_stressed_nodes:
        ssh = connect_remote_ssh(hostname)
        cmd_to_execute = "sudo docker pull "+ jupiter_config.STRESS_IMAGE
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute, get_pty=True)
        for line in ssh_stdout:
            print(line)
        cmd_to_execute = "sudo docker run -d --name sim "+ jupiter_config.STRESS_IMAGE
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute, get_pty=True)
        for line in ssh_stdout:
            print(line)
        cmd_to_execute = "sudo docker exec -it sim python3 /stress_test.py"
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute, get_pty=True)
        for line in ssh_stdout:
            print(line)

def prepare_stress_test():
    node_info_file = '../../nodes.txt'
    homes, nodes = get_nodes(node_info_file)
    build_push_stress()
    random_stressed_nodes = gen_random_stress(nodes)
    run_remote(random_stressed_nodes)
    
if __name__ == '__main__':
    prepare_stress_test()