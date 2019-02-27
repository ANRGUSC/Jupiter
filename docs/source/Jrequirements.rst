Requirements
============

In order to use the Jupiter Orchestrator tool, your computer needs to fulfill the following set of requirements.

- You MUST have ``kubectl`` installed (`instructions here <https://kubernetes.io/docs/tasks/tools/install-kubectl>`_ )

- You MUST have ``python3`` installed 

- You MUST have certain python packages (listed in ``k8_requirements.txt``) installed. You can install them by simply running 

.. code-block:: python
    :linenos:
    
    pip3 install -r k8_requirements.txt

- You MUST have a working kubernetes cluster with ``proxy`` capability.

- To control the cluster, you need to grab the ``admin.conf`` file from the k8s  master node. When the cluster is bootstrapped by ``kubeadm``, the ``admin.conf`` file is stored in ``/etc/kubernetes/admin.conf``. Usually, a copy is made into the ``$HOME`` folder. Either way, make a copy of ``admin.conf`` into your local machine's home folder. 

.. warning:: Currently, you need to have ``admin.conf`` file in the ``$HOME`` folder. Our python scripts need it exactly there to work.

- Next, you need to run the commands below. You can wrap it up in a script you source or directly place the export line and source line into your ``.bashrc`` file. However, make sure to re-run the full set of commands if the ``admin.conf`` file has changed:

.. code-block:: bash
   :linenos:

    sudo chown $(id -u):$(id -g) $HOME/admin.conf
    export KUBECONFIG=$HOME/admin.conf #check if it works with `kubectl get nodes`
    source <(kubectl completion bash)


- The directory structure of the cloned repo MUST conform with the following:

.. 
.. code-block:: text

        Jupiter
               │   jupiter_config.py 
               |   jupiter_config.ini
               |   nodes.txt
               │
               └───profilers
               │  
               └───task_mapper
               |   
               └───circe
               |
               └───app_specific_files
               |   |
               |   └───APP_folder
               |       |
               |       |   configuration.txt 
               |       |   app_config.ini 
               |       |
               |       └───scripts
               |       |
               |       └───sample_input
               |
               └───mulhome_scripts
               |___docs


