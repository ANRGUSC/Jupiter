Jupiter Evaluation
==================

We have built a runtime profiler for the purpose of gathering and analyzing relevant performance statistics while running Jupiter. The runtime profiler's purpose is to collect timestamp information either for all the tasks, compute nodes and incoming files, or file transfer process.  This built-in runtime profiler runs at the same time with the deployed system without any further actions. 


Automatic evaluation script
---------------------------
We wrote the optional script ``evaluate.py`` inside `CIRCE`_ , which you can choose to run or not in ``start_home.sh``. This script is only for testing purpose of `Coded DNAD`_ (Coded Network Anomaly Detection Application). After choosing this option and build the corresponding image, the script will be started automatically after ``CIRCE`` finishes dispatching all the tasks on all the computing nodes.


Collecting task performance statistics
--------------------------------------
This part of runtime profiler is integrated with `CIRCE`_ , the dispatcher tool of `Jupiter`_ You can find corresponding runtime profiler implementation in ``monitor.py`` and ``scheduler.py`` scripts of ``CIRCE``. Every compute node has a Flask server which can send related runtime information to the Flask server on the home node of ``CIRCE``. All the task-related runtime statistics are output at ``runtime_tasks.txt`` on the ``CIRCE home node`` under the following collumn-based format: ``Task_name``, ``local_input_file``, ``Enter_time``, ``Execute_time``, ``Finish_time,Elapse_time``, ``Duration_time``, ``Waiting_time``. This runtime file is only available after the ``evaluation.py`` finishes running. 

	- Enter time: time the input file enter the queue
	- Execute time: time the input file is processed
	- Finish time: time the output file is generated
	- Elapse time: total time since the input file is created till the output file is created
	- Duration time: total execution time of the task
	- Waiting time: total time since the input file is created till it is processed


Collecting file transfer performance statistics
-----------------------------------------------
This part of runtime profiler is implemented with the integration interface  `Jupiter`_, which servers the purpose of collecting runtime information of different data transfer methods in order for comparison. You can find corresponding runtime profiler implementation in ``CIRCE``integration inferface.

	- There are two options, whether collecting statistics only in the senders, or in both the senders and the receivers. This can be configured in ``jupiter_config.ini`` as the ``RUNTIME`` variable.  
	- All the data transfer related runtime statistics of the senders are output at ``runtime_transfer_sender.txt`` on each computing node under the following collumn-based format: ``Node_name, Transfer_Type, File_path, Time_stamp``. 
	- All the data transfer related runtime statistics of the receivers are output at ``runtime_transfer_receivers.txt`` on each computing node under the following collumn-based format: ``Node_name, Transfer_Type, File_path, Time_stamp``.
	- If the value of ``Time_stamp`` is ``-1``, it indicates that the file has not been transfered successfully; else it indicates the timestamp that the file starts to be transfered and the file has been transfered successfully.  



.. _CIRCE: https://github.com/ANRGUSC/Jupiter/tree/develop/circe
.. _Jupiter: https://github.com/ANRGUSC/Jupiter
.. _Coded DNAD: https://github.com/ANRGUSC/Coded-DNAD