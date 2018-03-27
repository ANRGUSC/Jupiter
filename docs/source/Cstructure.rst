Project Structure
=================

It is assumed that the folder ``circe/`` is located on the users home path (for example: ``/home/apac``). The structure of the project within ``circe/`` folder is the following:

.. code-block:: text

	- nodes.txt
	- dag.txt
	- configuration.txt (output of the HEFT algorithm)
	- profiler node1.txt, profiler node2.txt,... (output of execution profiler)
	- docker_execution_profiler/
	    - scheduler.py
	    - app/
	        - dag.txt
	        - requirements.txt
	        - Dockerfile
	        - DAG task files (task1.py, task2.py,...)
	        - DAG input file (input1.txt)
	        - start.sh
	        - profiler.py
	- centralized scheduler with profiler/
	    - input/ (this folder should be created by user)
	    - output/ (this folder should be created by user)
	    - 1botnet.ipsum, 2botnet.ipsum (example input files)
	    - scheduler.py
	    - monitor.py
	    - securityapp (this folder contains application task files, in this case localpro.py, aggregate0.py,...)
	    - removeprocesses.py
	    - remove_and_restart.py
	    - readconfig.py
	- heft/
	    - write_input_file.py
	    - heft_dup.py
	    - main.py
	    - create_input.py
	    - cpop.py
	    - read config.py
	    - input.tgff (output of write input file.py)
	    - readme.md
	- central network profiler/
	    - folder central_input: link list.txt, nodes.txt, central.txt
	    - central copy nodes
	    - central init
	    - central query statistics.py
	    - central scheduler.py
	    - folder network script: automate droplet.py, droplet generate random files, droplet init, droplet scp time transfer
	    - folder mongo control
	        - mongo scrip/
	          - server.py
	          - install package.py
	        - mongo control/
	          - insert to mongo.py
	          - read info.py
	          - read info.pyc
	          - install package.py
	          - jobs.py
	          - ip path


Note that while we currently use an implementation of HEFT for use with CIRCE, other schedulers may be used as well.