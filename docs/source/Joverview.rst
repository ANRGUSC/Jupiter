Overview
========

The Jupiter system has three main components: `DRUPE`_ (Network and Resource Profiler), `WAVE`_ Scheduler, and `CIRCE`_ Dispatcher.

.. _DRUPE: https://github.com/ANRGUSC/DRUPE
.. _WAVE: https://github.com/ANRGUSC/WAVE
.. _CIRCE: https://github.com/ANRGUSC/CIRCE

- `DRUPE`_ is a tool to collect information about computational resources as well as network links between compute nodes in a dispersed computing system to a central node. DRUPE consists of a network profiler and a resource profiler. 

- `WAVE`_ is a distributed scheduler for DAG type task graph that outputs a mapping of tasks to real compute nodes.

- `CIRCE`_ is a dispatcher tool for dispersed computing, which can deploy pipelined computations described in the form of a directed acyclic graph (DAG) on multiple geographically dispersed computers (compute nodes). CIRCE deploys each task on the corresponding compute node (from the output of WAVE), uses input and output queues for pipelined execution, and takes care of the data transfer between different tasks.
