Overview
========

**WAVE** is a distributed scheduler for DAG type task graph that outputs a mapping of tasks to real compute nodes. It is a module used in Jupiter. We have two versions `random_WAVE`_ and `greedy_WAVE`_

.. note:: We can not use WAVE as an independent tool

The code is open source, and `available on GitHub`_.

.. _available on GitHub: https://github.com/ANRGUSC/WAVE
.. _random_WAVE: https://github.com/ANRGUSC/WAVE/tree/master/random_wave
.. _greedy_WAVE: https://github.com/ANRGUSC/WAVE/tree/master/greedy_wave
.. _DRUPE: https://github.com/ANRGUSC/DRUPE

Description
-----------

Given a task graph that is represented as ``directed acyclic graph`` (DAG) and a network of ``network compute points`` (NCPs), the dispersed computing scheduler needs to figure out a mapping from the tasks to the NCPs with the goal **minimizing the average end-to-end latency of the incoming data-frames**. The scheduler needs to know the **computing resources availability** at each of the NCPs and the **qualities of the links** connecting any two devices in order to come up with a mapping.

-   The knowledge of the compute resources is important, since different tasks might be executed on different NCPs.
-   In such a case, the link quality knowledge is especially important as the output of a task being executed at an NCP will need to be shipped to its children task being executed at another NCP.

We consider the case where the scheduling is done in a distributed manner by multiple collaborating nodes located at different geographical locations. In such cases, each scheduling node only needs to know about its neighbours, their compute profiles and the link qualities to them.

WAVE components
---------------

Our scheduler is initialized by the WAVE master node, which has the information about the task graph. Based on the location of the input data, it determines the NCPs for each of the input tasks in the DAG. Also the master node determines a unique parent controller for each task in te task graph using following routine 1 shown below. At the WAVE master node, following routine is executed to determine the controllers for each task.

**Routine 1: Controller section routine**

-   Iterate over tasks of the the task graph in their topological orders.
-   For each non-input task, check if any of its parent tasks are already controllers.
-   If only one of the parents is already a controller, then appoint that parent as the controller for this task.
-   If no parent is already a controller, then choose the task with smaller topological index as the parent.

The task graph, input NCPs and parent controllers for each task are then sent to all NCPs. All NCPs are waiting to receive their task assignments. Whenever an NCP hears its task responsibility, it first needs to check if the assigned task is also a controller for any of the other tasks. The NCP can check this by looking up the parent controller information it has received from the WAVE master. If the NCP is a controller parent for some tasks of the task graph, it needs to do a NCP assignment for the children tasks. It runs following routine 2 to perform the child appointment.

**Routine 2: Scheduling algorithm at the controller**

-   Iterate over the children tasks in their topological orders.
-   For each task, randomly select an NCP from the neighbouring nodes.
-   Convey the task appointments to the selected NCPs and the WAVE master node.

When the WAVE master hears about all the task assignments, it starts the CIRCE deployment framework by providing the task graph and the mapping of these tasks to the compute nodes.

.. note:: Step 2 in routine 2 selects the NCPs randomly, however our system implementation is very modular and we are working on replacing it with a child appointment algorithm that considers the execution profiles of the neighbours, the link qualities connecting them and also the computing and communication requirements of the concerned tasks.

WAVE scheduling algorithms
--------------------------

Random WAVE
^^^^^^^^^^^

When assigning tasks to nodes, this version of **WAVE** does random assignment. The algorithm will random choose a node in the set of all validate nodes.

Greedy WAVE
^^^^^^^^^^^
When assigning tasks to nodes, this version of **WAVE** will first get network parameters from `DRUPE`_ as a delay factor. The delay factor contains network delay, target node's CPU usage and memory usage. The **WAVE** running in each of the node will maintain a sorted list of all its neighbor's delay information. Then it will pick up the node who has the lowest delay and assign tasks 
to it.


