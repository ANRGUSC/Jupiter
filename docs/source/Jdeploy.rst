Deploy instructions
===================

Step 1 : Clone Repo
-------------------

Clone or pull this repo and ``cd`` into the repo's directory. 

Step 2 : Update Node list
-------------------------

List of nodes for the experiment is kept in file ``nodes.txt`` 
(the user needs to fill the file with the appropriate **kubernetes nodenames** of their compute nodes). 

You can simply change just the hostnames in the given sample file. 
The first line should be 

.. code-block:: text

    home nodename

Everything else can be the same.

+-------+----------+
| home  | nodename |
+=======+==========+
| node1 | nodename |
+-------+----------+
| node2 | nodename |
+-------+----------+
| node3 | nodename |
+-------+----------+


Step 3 : Setup Home Node
------------------------

You need to setup the configurations for the circe home, wave home, and the central profiler.
For convienice we statically choose a node that will run all dockers.
To set that, you have to change the following line in your ``jupiter_config.py`` file. 

.. code-block:: python
    :linenos:

    HOME_NODE = 'ubuntu-2gb-ams2-04' 

This should point to a resource heavy node where you want to run them.
We kept it like this for convinience. However in future, this will be made dynamic as well. 
Next, we also need to point the child of CIRCE master. 
The CIRCE master is used to dispatch input files to tha DAG. 
Thus it should point to the ingress tasks of the DAG.  Change the following line in the config file to achieve that.

.. code-block:: python
    :linenos:

    HOME_CHILD = 'sample_ingress_task1'

For example, in the linked example of Network Monitoring, it is a single task called ``localpro``. 
But if there are multiple ingreass tasks, you have to put all of them by separating them by a ``:``.

Step 4 : Setup APP Folder
-------------------------

You need to make sure that you have a ``APP_folder`` with all the task specific files
inside the ``task_specific_files`` folder. The ``APP_folder`` needs to have a ``configuration.txt``,``app_config.ini`` and ``name_convert.txt``. 

The ``APP_folder`` MUST also contain all executable files of the task graph under the ``scripts`` sub-folder. 
You need to follow this exact folder structure to develop an APP for the Jupiter Orchestrator. 

.. note:: Detailed instructions for developing APPs for Jupiter will be posted later.

.. code-block:: text

    APP_folder
    |
    |   configuration.txt
    |   app_config.ini 
    |   name_convert.txt 
    |
    └───scripts
    |
    └───sample_input
        


Step 5 : Setup the Dockers
--------------------------

Version 2.0 and 3.0
^^^^^^^^^^^^^^^^^^^
Starting from version 2.0, to simplify the process we have provided with the following scripts:
    
.. code-block:: text
    :linenos:

    circe/circe_docker_files_generator.py --- prepare Docker files for CIRCE
    profilers/execution_profiler/exec_docker_files_generator.py --- for execution profiler
    profilers/network_resource_profiler/profiler_docker_files_generator.py --- for DRUPE 
    task_mapper/heft/heft_docker_files_generator.py --- for HEFT

These scripts will read the configuration information from ``jupiter_config.ini`` and ``jupiter_config.py`` to help generate corresponding Docker files for all the components. 

Version 4.0
^^^^^^^^^^^
The automatic scripts paths are updated:

.. code-block:: text
    :linenos:

    circe/original/circe_docker_files_generator.py --- prepare Docker files for CIRCE (nonpricing)
    circe/pricing_event/circe_docker_files_generator.py --- prepare Docker files for CIRCE (event driven pricing)
    circe/pricing_push/circe_docker_files_generator.py --- prepare Docker files for CIRCE (pushing pricing)
    profilers/execution_profiler_mulhome/exec_docker_files_generator.py --- for execution profiler
    profilers/network_resource_profiler/profiler_docker_files_generator.py --- for network profiler 
    task_mapper/heft_mulhome/original/heft_docker_files_generator.py --- for HEFT (original)
    task_mapper/heft_mulhome/modified/heft_docker_files_generator.py --- for HEFT (modified)
    task_mapper/wave_mulhome/greedy_wave/wave_docker_files_generator.py --- for WAVE (greedy)
    task_mapper/wave_mulhome/random_wave/wave_docker_files_generator.py --- for WAVE (random)


Step 6 : Choose the task mapper
-------------------------------

You must choose the Task Mapper from ``config.ini``. Currently, there are 4 options from the scheduling algorithm list: centralized (original HEFT, modified HEFT), distributed(random WAVE, greedy WAVE).

.. code-block:: text
    :linenos:

    [CONFIG]
        STATIC_MAPPING = 0
        SCHEDULER = 1

    [SCHEDULER_LIST]
        HEFT = 0
        WAVE_RANDOM = 1
        WAVE_GREEDY = 2
        HEFT_MODIFIED = 3

.. note:: When HEFT tries to optimize the Makespan by reducing communication overhead and putting many tasks on the same computing node, it ends up overloading them. While the Jupiter system can recover from failures, multiple failures of the overloaded computing nodes actually ends up adding more delay in the execution of the tasks as well as the communication between tasks due to temporary disruptions of the data flow. The modified HEFT is restricted to allocate no more than ``MAX_TASK_ALLOWED`` containers per computing node where the number ``MAX_TASK_ALLOWED`` is dependent upon the processing power of the node. You can find ``MAX_TASK_ALLOWED`` variable from ``heft_dup.py``. 

Step 7 : Optional - Choose the CIRCE dispatcher (only starting from Version 4) 
------------------------------------------------------------------------------

Starting from **Jupiter Version 4**, you must choose the CIRCE dispatcher from ``config.ini``. Currently, there are 3 options from the dispatcher list: nonpricing, pricing (event driven scheme, pushing scheme)


Step 8 : Optional - Modify the File Transfer Method or Network & Resource Monitor Tool
--------------------------------------------------------------------------------------

Select File Transfer method 
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Jupiter by default use ``SCP`` as the file transfer method. If you want to use any other file transfer tool instead (like ``XCP``, etc...), you can perform the following 2 steps:

Firstly, refer the :ref:`Integration Interface` and write your corresponding File Transfer module. 

Secondly, update ``config.ini`` to make Jupiter use your corresponding File Transfer method. 

.. code-block:: text
    :linenos:

    [CONFIG]
    TRANSFER = 0

    [TRANSFER_LIST]
    SCP = 0

Select Network & Resource Monitor Tool 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Jupiter by default use ``DRUPE`` as the Network & Resource Monitor Tool. If you want to use any other Network & Resource Monitor Tool, you can perform the following 2 steps:

Firstly, refer the :ref:`Integration Interface` and write your corresponding Network & Resource Monitor module. 

Secondly, update ``config.ini`` to make Jupiter use your corresponding Network & Resource Monitor module. 

.. code-block:: text
    :linenos:

    [CONFIG]
    PROFILER = 0

    [PROFILERS_LIST]
    DRUPE = 0

Step 9 : Push the Dockers
-------------------------

Now, you need to build your Docker images. 

To build Docker images and push them to the Docker Hub repo, first login 
to Docker Hub using your own credentials by running ``docker login``. Starting from **Jupiter Version 2**, we have provided with the following building scripts:

.. code-block:: text

    scripts/build_push_jupiter.py --- push all Jupiter related dockers
    scripts/build_push_circe.py --- Push CIRCE dockers only
    scripts/build push_profiler.py --- Push DRUPE dockers only
    scripts/build_push_wave.py --- Push WAVE dockers only
    scripts/build_push_heft.py --- Push HEFT dockers only
    scripts/build_push_exec.py --- Push execution profiler's  dockers only

The build path scripts are modified in **Jupiter Version 4**:
    
.. code-block:: text

    mulhome_scripts/build_push_jupiter.py --- push all Jupiter related dockers and nonpricing circe dispatcher
    mulhome_scripts/build_push_pricing_jupiter.py --- push all Jupiter related dockers and pricing circe dispatcher
    mulhome_scripts/build_push_circe.py --- Push nonpricing CIRCE dockers only
    mulhome_scripts/build_push_pricing_circe.py --- Push pricing CIRCE dockers only
    mulhome_scripts/build push_profiler.py --- Push DRUPE dockers only
    mulhome_scripts/build_push_wave.py --- Push WAVE dockers only
    mulhome_scripts/build_push_heft.py --- Push HEFT dockers only
    mulhome_scripts/build_push_exec.py --- Push execution profiler's  dockers only

.. warning:: However, before running any of these scripts you should update the ``jupiter_config`` file with your own docker names as well as dockerhub username. DO NOT run the script without crosschecking the config file.

Step 10 : Optional - Setup the Proxy (only required for Version 2 & 3)
----------------------------------------------------------------------

Now, you have to create a kubernetes proxy. You can do that by running the follwing command on a terminal.

.. code-block:: bash
    :linenos:
    
    kubectl proxy -p 8080


Step 11 : Create the Namespaces
-------------------------------

You need to create difference namespaces in your Kubernetes cluster 
that will be dedicated to the DRUPE, execution profiler, Task Mapper, and CIRCE deployments, respectively.
You can create these namespaces commands similar to the following:

.. code-block:: bash
    :linenos:

     kubectl create namespace johndoe-profiler
     kubectl create namespace johndoe-exec
     kubectl create namespace johndoe-mapper
     kubectl create namespace johndoe-circe

.. warning:: You also need to change the respective lines in the ``jupiter_config.py`` file.

.. code-block:: python
    :linenos:

    DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
    PROFILER_NAMESPACE      = 'johndoe-profiler'
    MAPPER_NAMESPACE        = 'johndoe-mapper'
    EXEC_NAMESPACE          = 'johndoe-exec'


Step 12 : Run the Jupiter Orchestrator
--------------------------------------


Next, you can simply run:

.. code-block:: bash
    :linenos:

    cd mulhome_scripts/
    python3 auto_deploy_system.py


Step 13 : Optional - Alternate scheduler
----------------------------------------

If you do not want to use our task mappers (``HEFT`` or ``WAVE``) for the scheduler and design your own, you can do that by simply using the ``static_assignment.py``. You must do that by setting ``STATIC_MAPPING`` to ``1`` from ``jupiter_config.ini``. You have to pipe your scheduling output to the ``static_assignment.py`` while conforming to the sample dag and sample schedule structure. Then you can run:

.. code-block:: bash
    :linenos:

    cd mulhome_scripts/
    python3 auto_deploy_system.py


Step 14 : Interact With the DAG
-------------------------------

Now you can interact with the pos using the kubernetes dashboard. 
To access it just pen up a browser on your local machine and go to 
``http://127.0.0.1:8080/ui``. You should see the k8s dashboard. 
Hit ``Ctrl+c`` on the terminal running the server to turn off the proxy. 
