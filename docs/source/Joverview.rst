Overview
********

Components
==========

The Jupiter system has three main components: Profilers, Scheduler Mapper and `CIRCE`_ Dispatcher.

- Profilers are tools used to collect information about the system.

	- `DRUPE`_ (Network and Resource Profiler) is a tool to collect information about computational resources as well as network links between compute nodes in a dispersed computing system to a central node. DRUPE consists of a network profiler and a resource profiler.

	- Execution profiler is a tool to collect the duration time as well as size of output files while performing a task on a specific computing node.

-  Scheduler Mapper is a tool to choose the specific scheduler as well as algorithm to be used for scheduling the tasks. 
	
	- `HEFT`_ (Heterogeneous Earliest Finish Time) is a popular centralized scheduling algorithm
	- `WAVE`_ is a distributed scheduler for DAG type task graph that outputs a mapping of tasks to real compute nodes. The current algorithm list includes random WAVE and greedy WAVE.

- `CIRCE`_ is a dispatcher tool for dispersed computing, which can deploy pipelined computations described in the form of a directed acyclic graph (DAG) on multiple geographically dispersed computers (compute nodes). CIRCE deploys each task on the corresponding compute node (from the output of WAVE), uses input and output queues for pipelined execution, and takes care of the data transfer between different tasks.

.. _DRUPE: https://github.com/ANRGUSC/DRUPE
.. _WAVE: https://github.com/ANRGUSC/WAVE
.. _CIRCE: https://github.com/ANRGUSC/CIRCE
.. _HEFT: https://en.wikipedia.org/wiki/Heterogeneous_Earliest_Finish_Time

The code is open source, and `available on GitHub`_.

.. _available on GitHub: https://github.com/ANRGUSC/Jupiter



Input
=====

File nodes.txt
--------------

This file lists all the nodes, line by line, in the following format:

+-------+----------+----------+-----+
| home  | nodename | username | pw  |
+=======+==========+==========+=====+
| node1 | nodename | username | pw  |
+-------+----------+----------+-----+
| node2 | nodename | username | pw  |
+-------+----------+----------+-----+
| node3 | nodename | username | pw  |
+-------+----------+----------+-----+

A given sample of node file:

.. figure::  images/nodes.png
   :align:   center


File jupiter_config.py
----------------------

This file includes all paths configuration for Jupiter system to start. The latest version of jupiter configuration file:

.. code-block:: text
    :linenos:

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

    NETR_PROFILER_PATH      = HERE + 'profilers/network_resource_profiler/'
    EXEC_PROFILER_PATH      = HERE + 'profilers/execution_profiler/'
    CIRCE_PATH              = HERE + 'circe/'
    HEFT_PATH               = HERE + 'task_mapper/heft/'
    WAVE_PATH               = HERE + 'task_mapper/wave/random_wave/'
    SCRIPT_PATH             = HERE + 'scripts/'

    if SCHEDULER == 1:
        WAVE_PATH           = HERE + 'task_mapper/wave/random_wave/'
    elif SCHEDULER == 2:
        WAVE_PATH           = HERE + 'task_mapper/wave/greedy_wave/'

    KUBECONFIG_PATH         = os.environ['KUBECONFIG']

    # Namespaces

    DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
    PROFILER_NAMESPACE      = 'johndoe-profiler'
    MAPPER_NAMESPACE        = 'johndoe-mapper'
    EXEC_NAMESPACE          = 'johndoe-exec'


    HOME_NODE               = get_home_node(HERE + 'nodes.txt')

    HOME_IMAGE              = 'docker.io/johndoe/home_node:v1'

    HOME_CHILD              = 'sample_ingress_task'

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

    # Application folder 
    APP_PATH                = HERE  + 'app_specific_files/network_monitoring_app/'
    APP_NAME                = 'app_specific_files/network_monitoring_app'

.. warning:: You need to create required namespaces in your Kubernetes cluster that will be dedicated to the profiler, scheduling mapper (to choose specific scheduling algorithms from HEFT, Random WAVE, greedy WAVE), and CIRCE deployments, respectively. You also need to update your namespace information correspondingly.

.. code-block:: python
    :linenos:
	
	DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
	PROFILER_NAMESPACE      = 'johndoe-profiler'
	MAPPER_NAMESPACE        = 'johndoe-mapper'
	EXEC_NAMESPACE          = 'johndoe-exec'

You also need to specify the corresponding information:

- CIRCE images : ``HOME_IMAGE`` and ``WORKER_IMAGE``
- DRUPE images : ``PROFILER_HOME_IMAGE`` and ``PROFILER_WORKER_IMAGE``
- Execution profiler images: ``EXEC_HOME_IMAGE`` and ``EXEC_WORKER_IMAGE``
- HEFT images: ``HEFT_IMAGE``
- WAVE images : ``WAVE_HOME_IMAGE`` and ``WAVE_WORKER_IMAGE``
- Initial task : ``HOME_CHILD``
- The application folder : ``APP_PATH``. The tasks specific files is recommended to be put in the folder ``task_specific_files``.

File config.ini
---------------

This file includes all configuration options for Jupiter system to start. The latest version of ``config.ini`` file includes types of mapping (static or dynamic), port information (SSH, Flask, Mongo), authorization (username and password), scheduling algorithm (Heft, random WAVE, greedy WAVE):

.. code-block:: text
    :linenos:

    [CONFIG]
        STATIC_MAPPING = 0
        SCHEDULER = 2
    [PORT]
        MONGO_SVC = 6200
        MONGO_DOCKER = 27017
        SSH_SVC = 5000
        SSH_DOCKER = 22
        FLASK_SVC = 6100
        FLASK_DOCKER = 8888
    [AUTH]
        USERNAME = root
        PASSWORD = PASSWORD
    [OTHER]
        MAX_LOG = 10
        NUM_NODES = 88
        SSH_RETRY_NUM = 20
    [SCHEDULER_LIST]
        HEFT = 0
        WAVE_RANDOM = 1
        WAVE_GREEDY = 2

.. warning:: You should specify the information in ``CONFIG`` section to choose the specific scheduling algorithm from the ``SCHEDULER_LIST``. ``STATIC_MAPPING`` is only chosen on testing purpose. 

File configuration.txt
----------------------

The tasks specific files is recommended to be put in the folder ``task_specific_files``. Inside the application folder, there should be a ``configuration.txt`` file having the DAG description. First line is an integer which gives the number of lines the DAG is taking. DAG is represented in the form of adjacency list:

.. code-block:: text
    :linenos:

    parent_task NUM_INPUTS FLAG child_task1 child_task2 child task3 ...


- ``parent_task`` is the name of the parent task

- ``NUM_INPUTS`` is an integer representing the number of input files the task needs in order to start processing (some tasks could require more than input).

- ``FLAG`` is ``true`` or ``false``. Based on its value, ``monitor.py`` will either send a single output of the task to all its children (when true), or it will wait the output files and start putting them into queue (when false). Once the queue size is equal to the number of children, it will send one output to one child (first output to first listed child, etc.).

- ``child_task1``, ``child_task2``, ``child_task3``... are the names of child tasks of the current parent task.

A given sample of application configuration file:

.. figure::  images/app_config.png
   :align:   center

Output
======

.. note:: Taking the node list from ``nodes.txt`` and DAG information from ``configuration.txt``, Jupiter will consider both updated network connectivity (from ``DRUPE-network profiler`` ) and computational capabilities (from ``DRUPE - resource profiler``) of all the nodes in the system, Jupiter use the chosen scheduling algorithm (``HEFT``, ``random WAVE`` or ``greedy WAVE``) to give the optimized mapping of tasks and nodes in the system. Next, ``CIRCE`` will handle deploying the optimized mapping in the **Kubernetes** system.



