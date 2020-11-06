# Jupiter v5.0

**Note**: Please see the the k8s_boostrap/mergetb directory for
instructions on how to bootstrap a MergeTB cluster. The provided ansible scripts
can be adapted and used to bootstrap clusters in other cloud providers.

Jupiter is an orchestrator for Dispersed Computing (distributed computing with
networked computers) that  uses Docker containers and Kubernetes (K8s).

Jupiter enables complex computing applications that are specified as directed
acyclic graph (DAG)-based task graphs to be distributed across an arbitrary
network of computers in such a way as to optimize the execution of the
distributed computation. Depending on the task mapper (i.e. scheduling
algorithm) used with the Jupiter framework, the optimizations may be for
different objectives. For example, the goal may be to try and minimize the total
end to end delay (makespan) of the computation for a single set of data inputs.
Jupiter includes both centralized task mappers such as one that performs the
classical HEFT (heterogeneous earliest finish time) scheduling algorithm, as
well as an innovative new distributed task mapping framework called WAVE.  In
order to enable optimization-oriented task mapping, Jupiter also provides tools
for profiling the application run time on the compute nodes as well as profiling
and monitoring the performance of network links between nodes. Jupiter is built
on top of Kubernetes and provides a container-based framework for the
dispatching and execution of distributed applications at run-time for both
single-shot and pipelined (streaming) computations.

The Jupiter system has three
main components:
 * Execution Profiler
 * DRUPE (Network Profiler)
 * Task Mappers
 * CIRCE (Dispatcher)


### Profilers
Jupiter comes with two different profiler tools: DRUPE (Network and Resource Profiler) and an one time Execution Profiler.

[DRUPE](https://github.com/ANRGUSC/DRUPE)  is a tool to collect information about computational
resources as well as network links between compute nodes in a dispersed
computing system to a central node. DRUPE consists of a network profiler and a
resource profiler.

The onetime Execution Profiler is a tool to collect information about the computation time of the pipelined computations
described in the form of a directed acyclic graph (DAG) on each of the networked computation resources. This tool runs a sample
execution of the entire DAG on every node to collect the statistics for each of the task in the DAG as well as the makespan of
the entire DAG.


### Task Mappers

Jupiter comes with three different task mappers: HEFT, WAVE Greedy, WAVE Random;
to effciently map the tasks of a DAG to the processors such that the makespan of
the pipelines processing is optimized.

[HEFT](https://github.com/oyld/heft.git) i.e., Heterogeneous Earliest Finish
Time is a static centralized algorithm for a DAG based task graph that
efficiently maps the tasks of the DAG into the processors by taking into account
global information about communication delays and execution times.

[WAVE](https://github.com/ANRGUSC/WAVE) is a distributed scheduler for DAG type
task graph that outputs a mapping of tasks to real compute nodes by only taking
into acount local profiler statistics. Currently we have two types of WAVE
algorithms: WAVE Random and WAVE Greedy.

WAVE Random is a very simple algorithm that maps the tasks to a random node
without taking into acount the profiler data.

WAVE Greedy is a Greedy algorithm that uses a weighted sum of different profiler
data to map tasks to the compute nodes.


### CIRCE

[CIRCE](https://github.com/ANRGUSC/CIRCE) is a dispatcher tool for dispersed computing,
which can deploy pipelined computations described in the form of a directed
acyclic graph (DAG) on multiple geographically dispersed computers (compute nodes).
CIRCE deploys each task on the corresponding compute node (from the output of WAVE),
uses input and output queues for pipelined execution,
and takes care of the data transfer between different tasks.




## Instructions

Currently supports: **Python 3.6**

First, setup your Kubernetes cluster and install
[`kubectl`](https://kubernetes.io/docs/tasks/tools/install-kubectl/). Enable
autocompletion for `kubectl`.

Clone and install requirements:

    git clone git@github.com:ANRGUSC/Jupiter.git
    cd Jupiter
    pip install -r k8s_requirements.txt

In the application `app_config.yaml` fill out the `node_map` key with the
hostnames of your k8s cluster. Set the `namespace_prefix` key and set the
`k8s_host` key for all tasks listed under the `nondag_tasks` key. See
`app_specific_files/example/app_config.yaml` for an example with instructions.

In `jupiter_config.py`, set `APP_NAME` to your application folder name under
`app_specific_files/`. Use `APP_NAME = "example"` for the example application.
Build all containers. *Run scripts in separate shells to parallelize*.

    cd core
    python build_push_exec.py
    python build_push_profiler.py
    python build_push_mapper.py
    python build_push_circe.py

Next, run the Execution Profiler, DRUPE (Network Profiler), and Task Mapper.
(Shortcut: for a quick start, you can look under `core/samples/` for an example
mapping.json file and create a custom one for your k8s cluster. Move it to
`core/mapping.json` and skip launching the profilers and mapper entirely.)

    python launch_exec_profiler.py
    python launch_net_profiler.py
    python launch_mapper.py

The Task Mapper will poll the DRUPE home pod until network profiling is
complete. This takes about 15 minutes. When it's done, `launch_mapper.py` will
exit and produce a `mapping.json` file under `core/`. You can shutdown the
profilers.

    python delete_all_exec.py
    python delete_all_profilers.py

CIRCE will use this to
launch the right task as a pod on the correct k8s node.

    python launch_circe.py

Use `kubectl logs -n={namespace_prefix}-circe` to read stdout of task
containers. To teardown your application,

    python delete_all_circe.py

If you make changes to anything under your application directory, you must
rebuild all CIRCE containers before re-running. For example after any code
change, you can redeploy using the same mapping.json by following these steps.

    python delete_all_circe.py
    python build_push_circe.py
    python launch_circe.py


## Applications:

Jupiter accepts pipelined computations described in a form of a Graph where the
main task flow is represented as a Directed Acyclic Graph (DAG). Jupiter also
allows the ability to orchestrate containers on specific nodes that are not part
of the main DAG. We differentiate the two as "DAG tasks" and "non-DAG tasks."

The example application under `app_specific_files/core` utilizes the key features
of Jupiter. Read the corresponding `app_config.yaml` to better understand the
components.

## References
[1] Pradipta Ghosh, Quynh Nguyen, and Bhaskar Krishnamachari, [“Container Orchestration for Dispersed Computing“](https://anrg.usc.edu/www/wp-content/uploads/2019/10/Jupiter__Camera_Ready.pdf), 5th International Workshop on Container Technologies and Container Clouds (WOC ’19), December 9–13, 2019, Davis, CA, USA.

[2] Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari, [“End-to-End Network Performance Monitoring for Dispersed
Computing“](http://anrg.usc.edu/www/papers/DispersedNetworkProfiler_ICNC2018.pdf), International Conference on Computing, Networking and Communications, March 2018


[3] Pranav Sakulkar, Pradipta Ghosh, Aleksandra Knezevic, Jiatong Wang, Quynh Nguyen, Jason Tran, H.V. Krishna Giri Narra,
Zhifeng Lin, Songze Li, Ming Yu, Bhaskar Krishnamachari, Salman Avestimehr, and Murali Annavaram, [“WAVE: A Distributed Scheduling
Framework for Dispersed Computing“](http://anrg.usc.edu/www/papers/wave_dispersed_computing_ANRGTechReport.pdf), USC ANRG Technical Report, ANRG-2018-01.

[4] Aleksandra Knezevic, Quynh Nguyen, Jason A. Tran, Pradipta Ghosh, Pranav Sakulkar, Bhaskar Krishnamachari, and Murali
Annavaram, [“DEMO: CIRCE – A runtime scheduler for DAG-based dispersed computing,”](http://anrg.usc.edu/www/papers/CIRCE__A_runtime_scheduler_for_DAG_based_dispersed_computing.pdf), The Second ACM/IEEE Symposium on Edge Computing
(SEC) 2017. (poster)


## Acknowledgment
This material is based upon work supported by Defense Advanced Research Projects Agency (DARPA) under Contract No. HR001117C0053.
Any views, opinions, and/or findings expressed are those of the author(s) and should not be interpreted as representing the
official views or policies of the Department of Defense or the U.S. Government.
