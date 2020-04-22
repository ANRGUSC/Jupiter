"""
Top level config file (leave this file at the root directory). ``import config`` on the top of your file to include the global information included here.
"""
__author__ = "Pradipta Ghosh, Quynh Nguyen, Pranav Sakulkar,  Jason A Tran, Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"


from os import path
import os
import configparser

HERE       = path.abspath(path.dirname(__file__)) + "/"
INI_PATH   = HERE + 'jupiter_config.ini'

def get_home_node(file_name):
    with open(file_name) as file:
        line = file.readline().split()
    return line[1]

def get_datasources(file_name):
    datasources = {}
    node_file = open(file_name, "r")
    for line in node_file:
        node_line = line.strip().split(" ")
        datasources.setdefault(node_line[0], [])
        for i in range(1, len(node_line)):
          datasources[node_line[0]].append(node_line[i])
    return datasources

def set_globals():
    """Set global configuration information
    """

    """Configuration Paths"""

    config = configparser.ConfigParser()
    config.read(INI_PATH)
    """User input for scheduler information"""
    global STATIC_MAPPING, SCHEDULER, TRANSFER, PROFILER, RUNTIME, PRICING, DCOMP

    STATIC_MAPPING          = int(config['CONFIG']['STATIC_MAPPING'])
    # scheduler option chosen from SCHEDULER_LIST
    SCHEDULER               = int(config['CONFIG']['SCHEDULER'])
    # transfer option chosen from TRANSFER_LIST
    TRANSFER                = int(config['CONFIG']['TRANSFER'])
    # Network and Resource profiler (TA2) option chosen from TA2_LIST
    PROFILER                = int(config['CONFIG']['PROFILER'])
    # Runtime profiling for data transfer methods: 0 for only senders, 1 for both senders and receivers
    RUNTIME                 = int(config['CONFIG']['RUNTIME'])
    # Using pricing or original scheme
    PRICING                 = int(config['CONFIG']['PRICING'])
    # Using dcomp
    DCOMP                   = int(config['CONFIG']['DCOMP'])


    """Authorization information in the containers"""
    global USERNAME, PASSWORD

    USERNAME                = config['AUTH']['USERNAME']
    PASSWORD                = config['AUTH']['PASSWORD']

    """Port and target port in containers for services to be used: Mongo, SSH and Flask"""
    global MONGO_SVC, MONGO_DOCKER, SSH_SVC, SSH_DOCKER, FLASK_SVC, FLASK_DOCKER, FLASK_CIRCE, FLASK_DEPLOY
    
    MONGO_SVC               = config['PORT']['MONGO_SVC']
    MONGO_DOCKER            = config['PORT']['MONGO_DOCKER']
    SSH_SVC                 = config['PORT']['SSH_SVC']
    SSH_DOCKER              = config['PORT']['SSH_DOCKER']
    FLASK_SVC               = config['PORT']['FLASK_SVC']
    FLASK_DOCKER            = config['PORT']['FLASK_DOCKER']
    FLASK_CIRCE             = config['PORT']['FLASK_CIRCE']
    FLASK_DEPLOY            = config['PORT']['FLASK_DEPLOY']

    global BOKEH,BOKEH_SERVER, BOKEH_PORT, BOKEH
    BOKEH = int(config['BOKEH_LIST']['BOKEH'])
    BOKEH_SERVER = config['BOKEH_LIST']['BOKEH_SERVER']
    BOKEH_PORT = int(config['BOKEH_LIST']['BOKEH_PORT'])
    BOKEH = int(config['BOKEH_LIST']['BOKEH'])
    

    """Modules path of Jupiter"""
    global NETR_PROFILER_PATH, EXEC_PROFILER_PATH, CIRCE_PATH, HEFT_PATH, WAVE_PATH, SCRIPT_PATH, STREAM_PATH, DATA_PATH

    # default network and resource profiler: DRUPE
    # default wave mapper: random wave
    NETR_PROFILER_PATH      = HERE + 'profilers/network_resource_profiler_mulhome/'
    EXEC_PROFILER_PATH      = HERE + 'profilers/execution_profiler_mulhome/'
    CIRCE_PATH              = HERE + 'circe/pricing/'
    HEFT_PATH               = HERE + 'task_mapper/heft_mulhome/original/'
    WAVE_PATH               = HERE + 'task_mapper/wave_mulhome/random_wave/'
    SCRIPT_PATH             = HERE + 'scripts/'
    # simulation of streaming data sources
    # STREAM_PATH             = HERE + 'simulation/data_sources/'
    # data sources for testing demo
    STREAM_PATH               = HERE + 'simulation/demo_sources/'

    global heft_option, wave_option
    heft_option             = 'original'    
    wave_option             = 'random' 


    if SCHEDULER == int(config['SCHEDULER_LIST']['WAVE_RANDOM']):
        print('Task mapper: Wave random selected')
        WAVE_PATH           = HERE + 'task_mapper/wave_mulhome/random_wave/'
        wave_option         = 'random'
    elif SCHEDULER == int(config['SCHEDULER_LIST']['WAVE_GREEDY']):
        print('Task mapper: Wave greedy (original) selected')
        WAVE_PATH           = HERE + 'task_mapper/wave_mulhome/greedy_wave/'
        wave_option         = 'greedy'
    elif SCHEDULER == int(config['SCHEDULER_LIST']['HEFT_BALANCE']):
        print('Task mapper: Heft load balanced selected')
        HEFT_PATH           = HERE + 'task_mapper/heft_mulhome/heft_balance/'   
        heft_option         = 'heftbalance'
    else: 
        print('Task mapper: Heft original selected')

    global pricing_option, profiler_option

    pricing_option          = 'original' #original pricing
    profiler_option         = 'multiple_home'

    if PRICING == int(config['PRICING_LIST']['NONPRICING']): #non-pricing
        pricing_option      = 'original'
        print('Non pricing scheme selected')
    if PRICING == int(config['PRICING_LIST']['PUSH_PRICING']):#multiple home (push circe)
        pricing_option      = 'pricing_push'
        print('Pricing pushing scheme selected')
    if PRICING == int(config['PRICING_LIST']['EVENT_PRICING']):#multiple home, pricing (event-driven circe)
        pricing_option      = 'pricing_event'
        print('Pricing event driven scheme selected')
    if PRICING == int(config['PRICING_LIST']['INTERGRATED_PRICING']): #new-pricing
        pricing_option      = 'integrated_pricing'
        print('Integrated pricing scheme selected')
    if PRICING == int(config['PRICING_LIST']['DECOUPLED_PRICING']): #new-pricing
        pricing_option      = 'decoupled_pricing'
        print('Decoupled pricing scheme selected')

    CIRCE_PATH              = HERE + 'circe/%s/'%(pricing_option)

    global cluster_option

    cluster_option          = 'do'
    if DCOMP == 1:
        cluster_option      = 'dcomp'

    
    """Kubernetes required information"""
    global KUBECONFIG_PATH, DEPLOYMENT_NAMESPACE, PROFILER_NAMESPACE, MAPPER_NAMESPACE, EXEC_NAMESPACE

    try:
        KUBECONFIG_PATH         = os.environ['KUBECONFIG']
    except Exception as e:
        print('KUBECONFIG environment variable has not been setup yet!')
    # Namespaces
    DEPLOYMENT_NAMESPACE    = 'quynh-circe'
    PROFILER_NAMESPACE      = 'quynh-profiler'
    MAPPER_NAMESPACE        = 'quynh-mapper'
    EXEC_NAMESPACE          = 'quynh-exec'

    """ Node file path and first task information """
    global HOME_NODE, HOME_CHILD, STREAM_NODE

    HOME_NODE               = get_home_node(HERE + 'nodes.txt')
    STREAM_NODE             = get_datasources(HERE + 'nodes.txt')
    

    """Application Information"""
    global APP_PATH, APP_NAME, APP_OPTION
    

    HOME_CHILD                = 'master_task'
    APP_PATH                  = HERE  + 'app_specific_files/demo/'
    APP_NAME                  = 'app_specific_files/demo'
    APP_OPTION                = 'demo'


    """pricing CIRCE home and worker images"""
    global PRICING_HOME_IMAGE, WORKER_CONTROLLER_IMAGE, WORKER_COMPUTE_IMAGE

    PRICING_HOME_IMAGE      = 'docker.io/anrg/%s_circe_home:%s_%s' %(pricing_option,APP_OPTION,cluster_option)
    WORKER_CONTROLLER_IMAGE = 'docker.io/anrg/%s_circe_controller:%s_%s' %(pricing_option,APP_OPTION,cluster_option)
    WORKER_COMPUTE_IMAGE  = 'docker.io/anrg/%s_circe_computing:%s_%s' %(pricing_option,APP_OPTION,cluster_option)

    global PRICING_HOME_CONTROLLER, PRICING_HOME_COMPUTE
    PRICING_HOME_CONTROLLER = 'docker.io/anrg/%s_circe_home_controller:%s_%s' %(pricing_option,APP_OPTION,cluster_option)
    PRICING_HOME_COMPUTE    = 'docker.io/anrg/%s_circe_home_compute:%s_%s' %(pricing_option,APP_OPTION,cluster_option)


    global NONDAG_CONTROLLER_IMAGE,NONDAG_WORKER_IMAGE # only required for non-DAG tasks (teradetectors and dft)
    NONDAG_CONTROLLER_IMAGE = 'docker.io/anrg/%s_circe_nondag:%s_%s' %(pricing_option,APP_OPTION,cluster_option)
    NONDAG_WORKER_IMAGE     = 'docker.io/anrg/%s_circe_nondag_worker:%s_%s' %(pricing_option,APP_OPTION,cluster_option)
    
    """CIRCE home and worker images for execution profiler"""
    global HOME_IMAGE, WORKER_IMAGE

    HOME_IMAGE              = 'docker.io/anrg/circe_home:%s_%s'%(APP_OPTION,cluster_option)
    WORKER_IMAGE            = 'docker.io/anrg/circe_worker:%s_%s'%(APP_OPTION,cluster_option)

    """DRUPE home and worker images"""
    global PROFILER_HOME_IMAGE, PROFILER_WORKER_IMAGE
    
    PROFILER_HOME_IMAGE     = 'docker.io/anrg/%s_profiler_home:coded_%s'%(profiler_option,cluster_option)
    PROFILER_WORKER_IMAGE   = 'docker.io/anrg/%s_profiler_worker:coded_%s'%(profiler_option,cluster_option)

    """WAVE home and worker images"""
    global WAVE_HOME_IMAGE, WAVE_WORKER_IMAGE

    #%s: random, v1: greedy

    WAVE_HOME_IMAGE         = 'docker.io/anrg/%s_%s_wave_home:%s_%s' %(wave_option,profiler_option,APP_OPTION,cluster_option)
    WAVE_WORKER_IMAGE       = 'docker.io/anrg/%s_%s_wave_worker:%s_%s' %(wave_option,profiler_option,APP_OPTION,cluster_option)

    """Execution profiler home and worker images"""
    global EXEC_HOME_IMAGE, EXEC_WORKER_IMAGE


    EXEC_HOME_IMAGE         = 'docker.io/anrg/%s_exec_home:%s_%s'%(profiler_option,APP_OPTION,cluster_option)
    EXEC_WORKER_IMAGE       = 'docker.io/anrg/%s_exec_worker:%s_%s'%(profiler_option,APP_OPTION,cluster_option)

    """HEFT docker image"""
    global HEFT_IMAGE

    HEFT_IMAGE              = 'docker.io/anrg/%s_heft:%s_%s'%(heft_option,APP_OPTION,cluster_option)
       

    global NUM_STRESS, STRESS_IMAGE
    NUM_STRESS = int(config['OTHER']['NUM_STRESS'])
    STRESS_IMAGE            = 'docker.io/anrg/stress:%s'%(cluster_option)

    global NUM_STREAM, STREAM_IMAGE
    NUM_STREAM = int(config['OTHER']['NUM_STREAM'])
    STREAM_IMAGE = 'docker.io/anrg/stream_home:%s_%s'%(APP_OPTION,cluster_option)

if __name__ == '__main__':
    set_globals()
