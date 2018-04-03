Userguide
*********

Profiling
=========

Execution profiler
------------------

- Description: produces ``profiler_nodeX.txt`` file for each node, which gives the execution time of each task on that node and the amount of data it passes to its child tasks. These results are required in the next step for HEFT algorithm.

- Input: ``dag.txt``, ``nodes.txt``, DAG task files (``task1.py``, ``task2.py``,. . . ), DAG input file (``input.txt``)

- Output: ``profiler_nodeNUM.txt``

- How to run

    -  Case 1: the file ``scheduler.py`` will copy the ``app`` folder to each of the nodes and execute the docker commands. Inside ``circe/docker_execution_profiler`` folder perform the following command:
        
    .. code-block:: python

    	python3 scheduler.py

    -  Case 2: copy the ``app`` folder to the each of the nodes using scp and inside ``app`` folder perform the following commands where hostname is the name of the node ( node1, node2, etc.).

    .. code-block:: bash

    	docker build –t profilerimage . docker run –h hostname profilerimage

    -  In both cases make sure that the command inside file ``app/start.sh`` gives the details (IP, username and password) of your scheduler machine.


Central network profiler
------------------------

- Description: automatically scheduling and logs communication information of all links betweet nodes in the network, which gives the quaratic regression parameters of each link representing the corresponding communication cost. These results are required in the next step for HEFT algorithm.

- Input: 

	- File ``central.txt`` stores credential information of the central node

	+----------------+----------+-----------+
	| CENTRAL IP     | USERNAME |  PASSWORD |
	+----------------+----------+-----------+
	| IP0            | USERNAME |  PASSWORD |
	+----------------+----------+-----------+

	- File ``nodes.txt`` stores credential information of the nodes information

	+-------+------------------------+---------+
	|TAG    |  NODE (username@IP)    | REGION  |
	+-------+------------------------+---------+
	|node1  |  username@IP1          | LOC1    |
	+-------+------------------------+---------+
	|node2  |  username@IP2          | LOC2    |
	+-------+------------------------+---------+
	|node3  |  username@IP3          | LOC3    |
	+-------+------------------------+---------+

	- File ``link_list.txt`` stores the the links between nodes required to log the communication

	+------------+----------------------+
	|SOURCE(TAG) |   DESTINATION(TAG)   |
	+------------+----------------------+
	|node1       |   node2              |
	+------------+----------------------+
	|node1       |   node3              |
	+------------+----------------------+
	|node2       |   node1              |
	+------------+----------------------+
	|node2       |   node3              |
	+------------+----------------------+
	|node3       |   node1              |
	+------------+----------------------+
	|node3       |   node2              |
	+------------+----------------------+

- Output: all quadratic regression parameters are stored in the local MongoDB on the central node.

- How to run:
	- At the central network profiler:
    
	    - Install required libraries: 

	    .. code-block:: bash

			./central_init 

	    - Inside the folder central, input add information about the nodes and the links.
	    
	    - Generate the scheduling files for each node, prepare the central database and collection, copy the scheduling information and network scripts for each node in the node list and schedule updating the central database every 10th minute.

	    .. code-block:: python

			python3 central scheduler.py 

	- At the droplets:

	    - The central network profiler copies all required scheduling files and network scripts to the folder online profiler in each droplet.
	     
	    - Install required libraries

	    .. code-block:: bash

			./droplet_init 

	    - Generate files with different sizes to prepare for the logging measurements, generate the droplet database, schedule logging measurement every minute and logging regression every 10th minute. (These parameters could be changed as needed.)

	    .. code-block:: python

		    python3 automate droplet.py


System resource profiler
------------------------


- Description: This Resource Profiler will get system utilization from all the nodes in the system. These information will then be sent to home node and stored into mongoDB.

- Output: The information includes: IP address of each node, cpu utilization of each node, memory utilization of each node, and the latest update time.

- How to run:

	- For working nodes: 

		- copy the ``Resource_Profiler_server`` folder to each working node using scp. 
		- In each node: 

		.. code-block:: python

			python2 Resource_Profiler_server/install_package.py

	- For scheduler node:

		- copy ``Resource_Profiler_control`` folder to home node using scp.
		- if a node’s IP address changes, just update the ``Resource_Profiler_control/ip_path`` file 
		- optional: inside ``Resource_Profiler_control`` folder: 

		.. code-block:: python
			:linenos:

			python2 install_package.py 
			python2 jobs.py &

	- Note: the content of ``ip_path`` are several lines of working nodes’ IP address. So if a node’s IP address is changed, make sure to update the ``ip_path`` file.

Heft
====

- Description: This HEFT implementation has been adapted/modified from [2].

- Input: HEFT implementation takes a file of .tgff format, which describes the DAG and its various costs, as input. The first step is to construct this (``input.tgff``) file from the input files ``dag.txt``, ``profiler_nodeNUM.txt``. From ``circe/heft/`` folder execute:

    .. code-block:: python

    	python write_input_file.py

- HEFT algorithm: This is the scheduling algorithm which decides where to run each task. It writes its output in a configuration file, needed in the next step by the run-time centralized scheduler. The algorithm takes input.tgff as an input and output the scheduling file ``configuration.txt``. From ``circe/heft/`` run:
    
    .. code-block:: python

    	python main.py
 

Centralized scheduler with profiler
===================================


- Centralized run-time scheduler. This is the run-time scheduler. It takes the configuration file ``configuration.txt``, given by HEFT, the node information ``nodes.txt`` and orchestrates the execution of tasks on given nodes, and output the DAG output files in ``circe/centralized_scheduler/output/`` folder. Inside ``circe/centralized_scheduler`` folder run:

    .. code-block:: python

    	python3 scheduler.py

- Wait several seconds and move ``input1.txt`` to ``apac_scheduler/centralized_scheduler/input/`` folder (repeat the same for other input files).

- Stopping the centralized run-time scheduler.  Run:

    .. code-block:: python

    	python3 removeprocesses.py

    This script will shh into every node and kill running processes, and kill the process on the master node.
    
- If network conditions change, one might want to restart the whole application. This can be done by running:

    .. code-block:: python
   
   		python3 remove_and_restart.py
 
    The first part of the script stops the system as described above. It then runs HEFT and restarts the centralized run-time scheduler with the new task-node mapping.
    
Run-time task profiler
======================


