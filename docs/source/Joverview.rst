Overview
********

Components
==========

`Jupiter`_ is an Orchestrator for Dispersed Computing that uses `Docker`_ containers and `Kubernetes`_ (K8s). 

Jupiter enables complex computing applications that are specified as directed acyclic graph (DAG)-based task graphs to be distributed across an arbitrary network of computers in such a way as to optimize the execution of the distributed computations. Depending on the scheduling algorithm/task mapper used with the Jupiter framework, the optimizations may be for different objectives, for example, the goal may be to try and minimize the total end to end delay (makespan) of the computation for a single set of data inputs. Jupiter includes both centralized task mappers such as one that performs the classical HEFT (heterogeneous earliest finish time) scheduling algorithm, as well as an innovative new distributed task mapping framework called WAVE. In order to do enable optimization-oriented task mapping, Jupiter also provides tools for profiling the application run time on the computers as well as profiling and monitoring the performance of the network. Jupiter also provides for container-based code dispatch and execution of the distributed application at run-time for both single-shot and pipelined (streaming) computations.

The Jupiter system has three main components: Profilers, Task Mapper and `CIRCE`_ Dispatcher.

- Profilers are tools used to collect information about the system.

	- `DRUPE`_ (Network and Resource Profiler) is a tool to collect information about computational resources as well as network links between compute nodes in a dispersed computing system to a central node. DRUPE consists of a network profiler and a resource profiler.

	- The onetime Execution Profiler is a tool to collect information about the computation time of the pipelined computations described in the form of a directed acyclic graph (DAG) on each of the networked computation resources. This tool runs a sample execution of the entire DAG on every node to collect the statistics for each of the task in the DAG as well as the makespan of the entire DAG.

-  Task Mapper comes with three different versions: HEFT, WAVE Greedy, WAVE Random; to effciently map the task controllers of a DAG to the processors such that the makespan of the pipelines processing is optimized.
	
	- `HEFT`_ Heterogeneous Earliest Finish Time is a static centralized algorithm for a DAG based task graph that efficiently maps the tasks of the DAG into the processors by taking into account global information about communication delays and execution times.
	- `WAVE`_ is a distributed scheduler for DAG type task graph that outputs a mapping of task controllers to real compute nodes by only taking into acount local profiler statistics. Currently we have two types of WAVE algorithms: WAVE Random and WAVE Greedy. WAVE Random is a very simple algorithm that maps the tasks to a random node without taking into acount the profiler data. WAVE Greedy is a Greedy algorithm that uses a weighted sum of different profiler data to map tasks to the most suitable nodes.

-  `CIRCE`_ is a dispatcher tool for dispersed computing, which can deploy pipelined computations described in the form of a directed acyclic graph (DAG) on multiple geographically dispersed computers (compute nodes). CIRCE uses input and output queues for pipelined execution, and takes care of the data transfer between different tasks. ``CIRCE`` comes with three different versions: nonpricing scheme, pricing event driven scheme and pricing push scheme.

    - ``Nonpricing CIRCE``: static version of dispatcher, which deploys each task controllers on the corresponding compute node given the output of the chosen Task mapper. The task controller is also responsible for the corresponding task itself. This is one-time scheduler. If the user wants to reschedule the compute nodes, he has to run the deploy script again (run corresponding Task mapper and CIRCE again).
    - ``Pricing Event driven CIRCE``: dynamic version of dispatcher, which deploys each task controllers on the corresponding compute node given the output of the chosen Task mapper. Moreover, the task controller will select the best current available compute node to perform the task it is responsible for based on the updated resource information (communication delays, execution times, compute resource availability, queue delays at each compute node). The update is performed at the time the task controllers receive the incoming streaming file, the task controllers request the update from the compute nodes. 
    - ``Pricing Pushing CIRCE``: similar to  `Pricing Event driven CIRCE``, but the update is performed in a different way, in which the compute nodes push the update to the task controllers every interval.


.. _Jupiter: https://github.com/ANRGUSC/Jupiter
.. _Docker: https://docs.docker.com/
.. _Kubernetes: https://kubernetes.io/docs/home/
.. _DRUPE: https://github.com/ANRGUSC/DRUPE
.. _WAVE: https://github.com/ANRGUSC/WAVE
.. _CIRCE: https://github.com/ANRGUSC/CIRCE
.. _HEFT: https://en.wikipedia.org/wiki/Heterogeneous_Earliest_Finish_Time

The code is open source, and `available on GitHub`_.

.. _available on GitHub: https://github.com/ANRGUSC/Jupiter

Applications
============

Jupiter accepts pipelined computations described in a form of a Graph where the main task flow is represented as a Directed
Acyclic Graph (DAG). Thus, one should be able separate the graph into two pieces, the DAG part and non-DAG part. Jupiter
requires that each task in the DAG part of the graph to be written as a Python function in a separate file under the scripts
folder. On the other hand the non-DAG tasks can be either Python function or a shell script with any number of arguments,
located under the scripts folder.

As an example, please refer to our codes available for the following applications customized for the Jupiter Orchestrator:

- Coded Network Anomaly Detection : `Coded DNAD`_ 
- Multi-Camera Processing DAG : `MCP DAG`_
- Automatic-DAG-Generator: `Dummy DAG`_ 

.. _Coded DNAD: https://github.com/ANRGUSC/Coded-DNAD
.. _MCP DAG: https://github.com/ANRGUSC/MCPDAG
.. _Dummy DAG: https://github.com/ANRGUSC/Automatic-DAG-Generator

In order to integrate one specific application into Jupiter, please refer to our documentation regarding Applications. 

Tutorials
==========

There are some provided tutorials:

- Set up kubernetes cluster on Digital Ocean: `set up k8s on DO`_
- Deploy Jupiter on Digital Ocean: `Jupiter deployment on DO`_
- Step by step instructions to set up Jupiter on a private network provided by Sean Griffin (Raytheon BBN Technologies): `private network setup`

.. _set up k8s on DO: https://www.youtube.com/watch?v=A5G0PpVcce0&feature=youtu.be
.. _Jupiter deployment on DO:  https://www.youtube.com/watch?v=k41m3CLvRjw
.. _private network setup: https://github.com/ANRGUSC/Jupiter/blob/develop/tutorial/Jupiter_setup.pdf











