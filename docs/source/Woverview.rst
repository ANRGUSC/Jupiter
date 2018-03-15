Overview
========

**WAVE** is a distributed scheduler for DAG type task graph that outputs a mapping of tasks to real compute nodes. It is a module used in Jupiter. We have two versions `random_WAVE`_ and `greedy_WAVE`_

Note: We can not use WAVE as an independent tool

The code is open source, and `available on GitHub`_.

.. _available on GitHub: https://github.com/ANRGUSC/WAVE
.. _random_WAVE: https://github.com/ANRGUSC/WAVE/tree/master/random_wave
.. _greedy_WAVE: https://github.com/ANRGUSC/WAVE/tree/master/greedy_wave
.. _DRUPE: https://github.com/ANRGUSC/DRUPE

Random WAVE
-----------

When assigning tasks to nodes, this version of WAVE does random assignment. The algorithm will random choose a node in the set of all validate nodes.

Greedy WAVE
-----------
When assigning tasks to nodes, this version of WAVE will first get network 
parameters from _`DRUPE` as a delay factor. The delay factor contains network delay, target node's CPU usage and memory usage. The WAVE running in each of the node will maintain a sorted list of all its neighbor's delay information. Then it will pick up the node who has the lowest delay and assign tasks 
to it.


