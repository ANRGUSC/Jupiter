Deploy instructions
===================

Step 1 : Clone Repo
-------------------

Clone or pull this repo and ``cd`` into the repo's directory. 

Step 2 : Update Node list
-------------------------

List of nodes for the experiment is kept in file ``nodes.txt`` 
(the user needs to fill the file with the appropriate **kubernetes nodenames,usernames and passwords** of their compute nodes). 
Note that, these usernames and passwords are actually the passwords for the dockers: Each line of the ``nodes.txt`` except the first line follow a format 

.. code-block:: text

    node#  nodename root password

You can simply change just the hostnames in the given sample file. 
The first line should be 

.. code-block:: text

    home nodename root password

Everything else can be the same.

+-------+----------+----------+-----+
| home  | nodename | username | pw  |
+=======+==========+==========+=====+
| node1 | nodename | username | pw  |
+-------+----------+----------+-----+
| node2 | nodename | username | pw  |
+-------+----------+----------+-----+
| node3 | nodename | username | pw  |
+-------+----------+----------+-----+


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
inside the ``task_specific_files`` folder. The ``APP_folder`` needs to have a configuration.txt and a DAG_Scheduler.txt. The configuration.txt is used by CIRCE while the DAG_Scheduler.txt is used by WAVE. 

.. warning:: We are currently working on merging these two files. 

The ``APP_folder`` MUST also contain all executable files of the task graph under the ``scripts`` sub-folder. 
You need to follow this exact folder structure to develop an APP for the Jupiter Orchestrator. 

.. note:: Detailed instructions for developing APPs for Jupiter will be posted later.

.. code-block:: text

    APP_folder
    |
    |   configuration.txt
    |   DAG_Scheduler.txt   
    |
    └───scripts
    |
    └───sample_input
        


Step 5 : Setup the Dockers
--------------------------

The dockerfiles can be found under the ``circe/`` folder.

Change the follwing lines in the ``home_node.Dockerfile`` to refer to your own app

.. code-block:: text
    :linenos:

    # Add input files
    COPY  task_specific_files/network_monitoring_app/sample_input /sample_input

    # Add the task speficific configuration files
    ADD task_specific_files/network_monitoring_app/configuration.txt /configuration.txt


Now you need to update the ``worker_node.Dockerfile`` to add your app specific
packages by changing the follwing lines:

.. code-block:: text
    :linenos:

    ## Install TASK specific needs. The hadoop is a requirement for the network profiler application

    RUN wget http://supergsego.com/apache/hadoop/common/hadoop-2.8.1/hadoop-2.8.1.tar.gz -P ~/

    RUN tar -zxvf ~/hadoop-2.8.1.tar.gz -C ~/


Also change the following line to refer to your app: 

.. code-block:: text

    ADD task_specific_files/network_monitoring_app/scripts/ /centralized_scheduler/


Step 6 : Push the Dockers
-------------------------

Now, you need to build your Docker images. 
There are currently six different docker images with two each for the profiler, wave, and circe.

To build Docker images and push them to the Docker Hub repo, first login 
to Docker Hub using your own credentials by running ``docker login``. Then, in the
folder with the ``*.Dockerfile`` files, use this template to build all the needed
Docker images:

.. code-block:: bash
    :linenos:

    docker build -f $target_dockerfile . -t $dockerhub_user/$repo_name:$tag
    docker push $dockerhub_user/$repo_name:$tag

Example:

.. code-block:: bash
    :linenos:

    docker build -f worker_node.Dockerfile . -t johndoe/worker_node:v1
    docker push johndoe/worker_node:v1
    docker build -f home_node.Dockerfile . -t johndoe/home_node:v1
    docker push johndoe/home_node:v1

The same thing needs to be done for the profiles and the WAVE files.

.. note:: To simplify the process we have provided with the following scripts:
    
.. code-block:: text

    scripts/build_push_jupiter.py --- push all Jupiter related dockers
    scripts/build_push_circe.py --- Push CIRCE dockers only
    scripts/build push_profiler.py --- Push DRUPE dockers only
    scripts/build_push_wave.py --- Push WAVE dockers only

.. warning:: However, before running any of these four script you should update the ``jupiter_config`` file with your own docker names as well as dockerhub username. DO NOT run the script without crosschecking the config file.

Step 7 : Setup the Proxy
------------------------

Now, you have to create a kubernetes proxy. You can do that by running the follwing command on a terminal.

.. code-block:: bash
    :linenos:
    
    kubectl proxy -p 8080


Step 8 : Create the Namespaces
------------------------------

You need to create three difference namespaces in your Kubernetes cluster 
that will be dedicated to the profiler, WAVE, and CIRCE deployments, respectively.
You can create these namespaces commands similar to the following:

.. code-block:: bash
    :linenos:

     kubectl create namespace johndoe-circe
     kubectl create namespace johndoe-profiler
     kubectl create namespace johndoe-wave

.. warning:: You also need to change the respective lines in the ``jupiter_config.py`` file.

.. code-block:: python
    :linenos:

    DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
    PROFILER_NAMESPACE      = 'johndoe-profiler'
    WAVE_NAMESPACE          = 'johndoe-wave'


Step 9 : Run the Jupiter Orchestrator
-------------------------------------

Next, you can simply run:

.. code-block:: bash
    :linenos:

    cd scripts/
    python3 k8s_jupiter_deploy.py


Step 9 : Alternate
------------------

If you do not want to use WAVE for the scheduler and design your own, you can do that by simply using the ``static_assignment.py`` and changing the ``static_mapping`` flag to ``True``. 
To that you have to pipe your scheduling output to the static_assignment.py while conforming to the sample dag and sample schedule structure. Then you can run:

.. code-block:: bash
    :linenos:

    cd scripts/
    python3 k8s_jupiter_deploy.py

Step 10 : Interact With the DAG
-------------------------------

Now you can interact with the pos using the kubernetes dashboard. 
To access it just pen up a browser on your local machine and go to 
``http://127.0.0.1:8080/ui``. You should see the k8s dashboard. 
Hit ``Ctrl+c`` on the terminal running the server to turn off the proxy. 
