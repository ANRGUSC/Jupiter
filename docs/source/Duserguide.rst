How to run
**********



Network Profiler
================


Non-dockerized version
----------------------

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



Dockerized version
------------------

- At the docker_online_profiler folder:
    
    - Modify input in folder ``central_input`` (``nodes.txt, link_list.txt``) of central_network_profiler and upload_docker_network accordingly (IP, PASSWORD, REG, link_list)

    - Upload codes to all the nodes and the central

    .. code-block:: bash

	    ./upload_docker_network  

    - Example run: Scheduler IP0, and other droplets IP1, IP2, IP3

- At the droplets, inside the droplet_network_profiler:

    - Build the docker: 

    .. code-block:: bash

	    docker build -t droplet_network_profiler .

    
    - Run the containers:

    .. code-block:: bash
      :linenos:

      docker run --rm --name droplet_network_profiler -t -i -e DOCKER_HOST=IP1 -p 5100:22 -P droplet_network_profiler

      docker run --rm --name droplet_network_profiler -t -i -e DOCKER_HOST=IP2 -p 5100:22 -P droplet_network_profiler

      docker run --rm --name droplet_network_profiler -t -i -e DOCKER_HOST=IP3 -p 5100:22 -P droplet_network_profiler

- At the central network profiler (IP0):
     
    - Build the docker: 

    .. code-block:: bash

	    docker build -t central_network_profiler .

    - Run the container:

    .. code-block:: bash

    	docker run --rm --name  central_network_profiler -i -t -e DOCKER_HOST=IP0 -p 5100:22 -P central_network_profiler


Kubernetes Version of Network Profiler
--------------------------------------

Run from scratch
^^^^^^^^^^^^^^^^

- The instructions here begin at the point in which you have a target ``configuration.txt`` and ``nodes.txt`` file. First, you need to build your Docker images. There are currently two separate images: the ``central_profiler`` image and ``worker_profiler`` image.

- To rebuild Docker images and push them to the ANRG Docker Hub repo, first login to Docker Hub using your own credentials by running ``docker login``. Then, in the folder with the Dockerfile files, use this template to build all the needed Docker images:


.. code-block:: bash
   :linenos:

   docker build -f $target_dockerfile . -t $dockerhub_user/$repo_name:$tag
   docker push $dockerhub_user/$repo_name:$tag

- Example:

.. code-block:: bash
   :linenos:

   docker build -f Network_Profiler/central_network_profiler/Dockerfile . -t anrg/central_profiler:v1
   docker push anrg/central_profiler:v1
   docker build -f Network_Profiler/droplet_network_profiler/Dockerfile . -t anrg/worker_profiler:v1
   docker push anrg/worker_profiler:v1

- Note: If you just want to control the whole cluster via our master node (i.e. you don't want to use your computer) go to `this section`_   in the readme).

.. _this section: #controlling-cluster-from-k8s-master-node

- To control the cluster, you need to grab the ``admin.conf`` file from the k8s master node. When the cluster is bootstrapped by ``kubeadm`` `see the k8s cluster setup notes here`_ the ``admin.conf`` file is stored in ``/etc/kubernetes/admin.conf``. Usually, a copy is made into the ``$HOME`` folder. Either way, make a copy of ``admin.conf`` into your local machine's home folder. Then, make sure you have ``kubectl`` installed `instructions here`_. 

.. _see the k8s cluster setup notes here: https://drive.google.com/open?id=1NeewrSx9Bp3oNOGGpgyfKBjul1NbSB8kHqy7gslxtKk

.. _instructions here: https://kubernetes.io/docs/tasks/tools/install-kubectl/


- Next, you need to run the commands below. You can wrap it up in a script you source or directly place the export line and source line into your .bashrc file. However, make sure to re-run the full set of commands if the ``admin.conf`` file has changed:

.. code-block:: bash
   :linenos:

   sudo chown $(id -u):$(id -g) $HOME/admin.conf
   export KUBECONFIG=$HOME/admin.conf #check if it works with `kubectl get nodes`
   source <(kubectl completion bash)

	    

- Clone or pull this repo and ``cd`` into the repo's directory. Currently, you need to have ``admin.conf`` in the folder above your clone. Our python scripts need it exactly there to work. Then, run:

.. code-block:: python

   python3 k8s_profiler_scheduler.py

Then wait for a bit like 2-3 min for all the worker dockers to be up and running. Then run:

.. code-block:: python

   python3 k8s_profiler_home_scheduler.py


- Lastly, you will want to access the k8s Web UI on your local machine. Assuming you have ``kubectl`` installed and ``admin.conf`` imported, simply open a separate terminal on your local machine and run:

.. code-block:: python

   kubectl proxy
    	

- The output should be something like:

.. code-block:: text

   Starting to serve on 127.0.0.1:8001

- Open up a browser on your local machine and go to ``http://127.0.0.1:8001/ui``. You should see the k8s dashboard. Hit ``Ctrl+c`` on the terminal running the server to turn off the proxy. Alternatively, you can run this command directly in the folder where the ``admin.conf`` file is (not recommended):

.. code-block:: bash

   kubectl --kubeconfig=./admin.conf proxy - p 80


Teardown
^^^^^^^^

- To teardown the DAG deployment, run the following:
    
.. code-block:: python

	python3 delete_all_profilers.py

- Once the deployment is torn down, you can simply start from the begining of these instructions to make changes to your code and redeploy the DAG. FYI, k8s_scheduler.py defaults to ALWAYS pulling the Docker image (even if it hasn't changed).

Controlling Cluster from K8s Master Node
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Login to the Kubernetes Master node (currently Jason's computer under the user ``apac``). Assuming the cluster is up (it typically will not be shutdown), source the sourceit.sh script in the ``apac`` user's home folder so you can use ``kubectl`` to  control the cluster:
    
.. code-block:: bash

	source sourceit.sh

- Note that you do NOT need to do this if the ``admin.conf`` file hasn't changed  given the following lines are placed in the master node's .bashrc file:

.. code-block:: bash

    export KUBECONFIG=$HOME/admin.conf
    source <(kubectl completion bash)

The ``admin.conf`` file changes whenever the cluster is re-bootstrapped. You can 
then run the following command to check if everything is working. If it lists 
all the nodes in the cluster, you're ready to start controlling it:

.. code-block:: bash

	kubectl get nodes #if this works you're ready to start Controlling

Resource Profiler
=================

Non-dockerized version
----------------------

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

- Note: the content of ip_path are several lines of working nodes’ IP address. So if a node’s IP address is changed, make sure to update the ip_path file.

Dockerized-version
------------------

- For working nodes: 
	
	- copy the ``Resource_Profiler_server_docker`` folder to each working node using scp.
	- in each node:

	.. code-block:: bash
	   :linenos:
	   
	   docker build -t server . 
	   docker run -d -p 49155:5000 server

- For scheduler node:

	- copy ``Resource_Profiler_control_docker`` folder to home node using scp.
	- if a node’s IP address changes, just update the ``Resource_Profiler_control_docker/control_file/ip_path`` file 
	- optional: find central_network_profiler container Get the IP address. 

	.. code-block:: bash

		docker inspect CONTAINER ID

	- type mongo IP and then inside mongo shell. 

	.. code-block:: bash

		use DBNAME db.createUser({ user: 'USERNAME', pwd: 'PASSWORD', roles: [{ role: 'readWrite', db:'DBNAME'}] }}

	- inside ``Resource_Profiler_control_docker`` folder: 

	.. code-block:: bash

		docker build -t control . docker run control

- Note: the content of ip_path are several lines of working nodes’ IP address. So if a node’s IP address is changed, make sure to update the ip_path file.
