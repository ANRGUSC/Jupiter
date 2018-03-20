"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh
 *      Quynh Nguyen
 *      Pranav Sakulkar
 *      Jason A Tran
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""
# Top level config file (leave this file at the root directory). `import config`
# on the top of your file to include the global information included here.

from os import path
import os
import configparser

def get_home_node(file_name):
    with open(file_name) as file:
        line = file.readline().split()
    return line[1]


HERE                    = path.abspath(path.dirname(__file__)) + "/"
INI_PATH                = HERE + 'jupiter_config.ini'

config = configparser.ConfigParser()
config.read(INI_PATH)

STATIC_MAPPING          = int(config['CONFIG']['STATIC_MAPPING'])
SCHEDULER               = int(config['CONFIG']['SCHEDULER'])

USERNAME                = config['AUTH']['USERNAME']
PASSWORD                = config['AUTH']['PASSWORD']

MONGO_SVC               = config['PORT']['MONGO_SVC']
MONGO_DOCKER            = config['PORT']['MONGO_DOCKER']
SSH_SVC                 = config['PORT']['SSH_SVC']
SSH_DOCKER              = config['PORT']['SSH_DOCKER']
FLASK_SVC               = config['PORT']['FLASK_SVC']
FLASK_DOCKER            = config['PORT']['FLASK_DOCKER']
PYTHON_PORT             = config['PORT']['PYTHON_PORT']

PROFILER_PATH           = HERE + 'profilers/'
CIRCE_PATH              = HERE + 'circe/'
EXEC_PATH               = HERE + 'exec_profiler/'
HEFT_PATH               = HERE + 'heft/'

if SCHEDULER == 1:
    WAVE_PATH           = HERE + 'wave/random_wave/'
elif SCHEDULER == 2:
    WAVE_PATH           = HERE + 'wave/greedy_wave/'

KUBECONFIG_PATH         = os.environ['KUBECONFIG']

# Namespaces

DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
PROFILER_NAMESPACE      = 'johndoe-profiler'
MAPPER_NAMESPACE        = 'johndoe-wave'
EXEC_NAMESPACE          = 'johndoe-exec'


HOME_NODE               = get_home_node('nodes.txt')

HOME_IMAGE              = 'docker.io/johndoe/home_node:v1'

HOME_CHILD              = 'sample_ingress_task1'

WORKER_IMAGE            = 'docker.io/johndoe/worker_node:v1'

# Profiler docker image
PROFILER_HOME_IMAGE     = 'docker.io/johndoe/central_profiler:v1'
PROFILER_WORKER_IMAGE   = 'docker.io/johndoe/worker_profiler:v1'

# WAVE docker image
WAVE_HOME_IMAGE         = 'docker.io/johndoe/wave_home:v1'
WAVE_WORKER_IMAGE       = 'docker.io/johndoe/wave_worker:v1'

# Execution profiler  docker image
EXEC_HOME_IMAGE         = 'docker.io/johndoe/exec_home:v1'
EXEC_WORKER_IMAGE       = 'docker.io/johndoe/exec_worker:v1'

# Heft docker image
HEFT_IMAGE              = 'docker.io/johndoe/heft:v1'

APP_PATH                = HERE  + 'task_specific_files/network_monitoring_app/'
APP_NAME                = 'task_specific_files/network_monitoring_app'
