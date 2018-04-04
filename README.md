# Jupiter  

Jupiter is a orchestrator for Dispersed Computing that 
uses Docker containers and Kubernetes (K8s).  The Jupiter system has three
main components: Profilers, Task Mappers, and
CIRCE Dispatcher. **(For a detailed documentation refer to our [http://jupiter.readthedocs.io/](http://jupiter.readthedocs.io/))**



### Profilers
Jupiter comes with two different profiler tools: DRUPE (Network and Resource Profiler) and an one time Execution Profiler.

[DRUPE](https://github.com/ANRGUSC/DRUPE)  is a tool to collect information about computational
resources as well as network links between compute nodes in a dispersed
computing system to a central node. DRUPE consists of a network profiler and a
resource profiler.

The onetime Execution Profiler is a tool to collect information about the computation time of the pipelined computations described in the form of a directed acyclic graph (DAG) on each of the networked computation resources. This tool runs a sample execution of the entire DAG on every node to collect the statistics for each of the task in the DAG as well as the makespan of the entire DAG. 


### Task Mappers
Jupiter comes with three different task mappers: HEFT, WAVE Greedy, WAVE Random; to effciently map the tasks of a DAG to the processors such that the makespan of the pipelines processing is optimized.

[HEFT](https://github.com/oyld/heft.git) i.e., Heterogeneous Earliest Finish Time is a static centralized algorithm for a DAG based task graph that efficiently maps the tasks of the DAG into the processors by taking into account global information about communication delays and execution times.

[WAVE](https://github.com/ANRGUSC/WAVE) is a distributed scheduler for DAG type
task graph that outputs a mapping of tasks to real compute nodes by only taking into acount local profiler statistics.
Currently we have two types of WAVE algorithms: WAVE Random and WAVE Greedy.

WAVE Random is a very simple algorithm that maps the tasks to a random node without taking into acount the profiler data.

WAVE Greedy is a Greedy algorithm that uses a weighted sum of different profiler data to map tasks to the compute nodes.


### CIRCE

[CIRCE](https://github.com/ANRGUSC/CIRCE) is a dispatcher tool for dispersed computing,
which can deploy pipelined computations described in the form of a directed
acyclic graph (DAG) on multiple geographically dispersed computers (compute nodes).
CIRCE deploys each task on the corresponding compute node (from the output of WAVE),
uses input and output queues for pipelined execution,
and takes care of the data transfer between different tasks.



## Clone Instructions:
This Repository comes with a submodule with links to another repository that
contains codes related to one application (Distributed Network Anomaly Detection)
of Jupiter.

If you are interested in cloning just the Jupiter Orchestrator, not the application
specific files, just run 

```
    git clone git@github.com:ANRGUSC/Jupiter.git
```

If you are interested in cloning the Jupiter Orchestrator along with the Distributed 
Network Anomaly Detection related files, run 

```
    git clone --recurse-submodules git@github.com:ANRGUSC/Jupiter.git
    cd Jupiter
    git submodule update --remote
```

## Requirements:
In order to use the Jupiter Orchestrator tool, your computer needs to fulfill the following set of requirements.

1) You MUST have `kubectl` installed ([instructions 
here](https://kubernetes.io/docs/tasks/tools/install-kubectl/))

2) You MUST have `python3` installed 

3) You MUST have certain python packages (listed in k8_requirements.txt) installed.
You can install them by simply running ```pip3 install -r k8_requirements.txt```

4) You MUST have a working kubernetes cluster with `proxy` capability.

5) To control the cluster, you need to grab the `admin.conf` file from the k8s 
master node. When the cluster is bootstrapped by `kubeadm`, the `admin.conf` file is stored in `/etc/kubernetes/admin.conf`. Usually, a copy
is made into the $HOME folder. Either way, make a copy of `admin.conf` into your 
local machine's home folder. 
**Currently, you need to have `admin.conf` in the $Home folder. Our python scripts need it exactly
there to work.**
Next, you need to run the commands below. You can wrap it up in a script you source or directly 
place the export line and source line into your `.bashrc` file. However, make sure 
to re-run the full set of commands if the `admin.conf` file has changed:
``` sudo chown $(id -u):$(id -g) $HOME/admin.conf
    export KUBECONFIG=$HOME/admin.conf #check if it works with `kubectl get nodes`
    source <(kubectl completion bash)
```
5) The directory structure of the cloned repo MUST conform with the following:
```
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
        └───scripts

```


## Deploy Instructions:

For a step by step instruction for deployment of Jupiter, please refer to our [tutorial](http://jupiter.readthedocs.io/en/latest/Jdeploy.html). 

## Applications:

 Jupiter accepts pipelined computations described in a form of a Graph where the main task flow is represented as a Directed Acyclic Graph(DAG). Thus, one should be able separate the graph into two pieces, the DAG part and non-DAG part. Jupiter requires that each task in the DAG part of the graph to be written as a Python function in a separate file under the scripts folder. On the other hand the non-DAG tasks can be either Python function or a shell script with any number of arguments, located under the scripts folder.

 As an example, please refer to our codes available for an application called the Coded Network Anomaly Detection ([Coded DNAD](https://github.com/ANRGUSC/Coded-DNAD)). This is an application customized for the Jupiter Orchestrator.

## Visualization

The visualization tool for Jupiter is given [here](https://github.com/ANRGUSC/Jupiter_Visualization ). This tool generates an interactive plot to show the scheduling result of WAVE and the dispatcher mapping of CIRCE. To visualize your own application, make sure the format of your logs are in line with the input files of the tools. We will integrate this as a real-time visualization tool for Jupiter in the next release.  

## References
[1] Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari, “End-to-End Network Performance Monitoring for Dispersed Computing“, International Conference on Computing, Networking and Communications, March 2018

[2] Aleksandra Knezevic, Quynh Nguyen, Jason A. Tran, Pradipta Ghosh, Pranav Sakulkar, Bhaskar Krishnamachari, and Murali Annavaram, “DEMO: CIRCE – A runtime scheduler for DAG-based dispersed computing,” The Second ACM/IEEE Symposium on Edge Computing (SEC) 2017. (poster)

[3] Pranav Sakulkar, Pradipta Ghosh, Aleksandra Knezevic, Jiatong Wang, Quynh Nguyen, Jason Tran, H.V. Krishna Giri Narra, Zhifeng Lin, Songze Li, Ming Yu, Bhaskar Krishnamachari, Salman Avestimehr, and Murali Annavaram, “WAVE: A Distributed Scheduling Framework for Dispersed Computing“, USC ANRG Technical Report, ANRG-2018-01.

## Acknowledgment
This material is based upon work supported by Defense Advanced Research Projects Agency (DARPA) under Contract No. HR001117C0053. Any views, opinions, and/or findings expressed are those of the author(s) and should not be interpreted as representing the official views or policies of the Department of Defense or the U.S. Government.
