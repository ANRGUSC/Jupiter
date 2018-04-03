Overview
========

**DRUPE**  is a tool to collect information about computational resources as well as network links between compute nodes in a dispersed computing system to a central node. DRUPE consists of a network profiler and a resource profiler.

.. note:: We can use DRUPE as an independent tool.

The code is open source, and `available on GitHub`_.

.. _available on GitHub: https://github.com/ANRGUSC/DRUPE


Network Profiler
----------------

Description
^^^^^^^^^^^

The network profiler in DRUPE automatically schedules and logs communication information of all links between nodes in the network, which gives the quadratic regression parameters of each link representing the corresponding communication cost. The quadratic function represents how the file transfer time depends on the file size (based on our empirical finding that a quadratic function is a good fit.)

Versions
^^^^^^^^

-  `Non dockerized implementation`_
-  `Dockerized implementation`_
-  `Kubernetes implementation`_

.. _Non dockerized implementation: https://github.com/ANRGUSC/DRUPE/tree/master/DCP
.. _Dockerized implementation: https://github.com/ANRGUSC/DRUPE/tree/master/Docker_DCP
.. _Kubernetes implementation: https://github.com/ANRGUSC/DRUPE/tree/master/K8_DCP

Input
^^^^^

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

- File ``generate_link_list.py`` is used to generate file ``link_list.txt`` (all combinations of links) from the node list in file ``nodes.txt``, or users can customize the ``link_list.txt`` on their own.

Output
^^^^^^

All quadratic regression parameters are stored in the local MongoDB server on the central node.

Resource Profiler
-----------------

Description
^^^^^^^^^^^

This Resource Profiler will get system utilization from all the nodes in the system. These information will then be sent to home node and stored into mongoDB.

Output
^^^^^^
The information includes: IP address of each node, cpu utilization of each node, memory utilization of each node, and the latest update time.

