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

DEPLOYMENT_NAMESPACE    = 'pranav-circe'
PROFILER_NAMESPACE      = 'pranav-profiler'
MAPPER_NAMESPACE        = 'pranav-wave'
EXEC_NAMESPACE          = 'pranav-exec'

#home's child node is hardcoded in write_circe_home_specs.py
HOME_NODE               = 'ubuntu-s-1vcpu-3gb-fra1-09'

HOME_IMAGE              = 'docker.io/anrg/home_node:q1'

HOME_CHILD              = 'localpro'

WORKER_IMAGE            = 'docker.io/anrg/worker_node:q1'

# Profiler Path
PROFILER_HOME_IMAGE     = 'docker.io/anrg/central_profiler:q1'
PROFILER_WORKER_IMAGE   = 'docker.io/anrg/worker_profiler:q1'

# WAVE scheduler variables
WAVE_HOME_IMAGE         = 'docker.io/anrg/wave_home:q1'
WAVE_WORKER_IMAGE       = 'docker.io/anrg/wave_worker:q1'

# Execution Profiler Path
EXEC_HOME_IMAGE         = 'docker.io/anrg/exec_home:q1'
EXEC_WORKER_IMAGE       = 'docker.io/anrg/exec_worker:q1'

# Heft Path
HEFT_IMAGE              = 'docker.io/anrg/heft:p1'

APP_PATH                = HERE  + 'task_specific_files/network_monitoring_app/'
APP_NAME                = 'task_specific_files/network_monitoring_app'
