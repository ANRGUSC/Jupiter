# Jupiter  

Jupiter is a Central orchestrator for Dispersed Computing Platform
that uses Docker containers and Kubernetes (K8s).  The Jupiter system has three
main components: DRUPE (Network and Resource Profiler), WAVE Scheduler, and
CIRCE Dispatcher.  

[DRUPE](https://github.com/ANRGUSC/DRUPE)  is a tool to collect information about computational
resources as well as network links between compute nodes in a dispersed
computing system to a central node. DRUPE consists of a network profiler and a
resource profiler.

[WAVE](https://github.com/ANRGUSC/WAVE) is a distributed scheduler for DAG type
task graph that outputs a mapping of tasks to real compute nodes.

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
        |   nodes.txt
        │
        └───profilers
        │  
        └───wave
        |   
        └───circe
        |
        └───task_specific_files
        |   |
        |   └───APP_folder
        |       |
        |       |   configuration.txt
        |       |   DAG_Scheduler.txt   
        |       |
        |       └───scripts
        |       |
        |       └───sample_input
        |
        └───scripts

```


## Deploy Instructions:

### Step 1 (Clone Repo)
Clone/pull this repo and `cd` into the repo's directory. 

### Step 2 (Update Node list)
List of nodes for the experiment is kept in file nodes.txt 
(the user needs to fill the file with the appropriate kubernetes nodenames,
usernames and passwords of their compute nodes). 
Note that, these usernames and passwords are actually the passwords for the dockers:
Each line of the `nodes.txt` except the first line follow a format 
``` node#  nodename root password```
You can simply change just the hostnames in the given sample file. 
The first line should be ``` home nodename root password```
Everything else can be the same.

| home | nodename |username | pw |
| ------ |----|--|-- |
| node1 | nodename| username |pw |
| node2 | nodename| username| pw |
| node3  | nodename |username |pw |


### Step 3 (Setup Home Node)

You need to setup the configurations for the circe home, wave home, and the central profiler.
For convienice we statically choose a node that will run all dockers.
To set that, you have to change the following line in your `jupiter_config.py` file. 

```
    HOME_NODE               = 'ubuntu-2gb-ams2-04' 
```
This should point to a resource heavy node where you want to run them.
We kept it like this for convinience. However in future, this will be made dynamic as well. 
Next, we also need to point the child of CIRCE master. 
The CIRCE master is used to dispatch input files to tha DAG. 
Thus it should point to the ingress tasks of the DAG.  Change the following line in the config file to achieve that.
```
    HOME_CHILD              = 'sample_ingress_task1'
```
For example, in the linked example of Network Monitoring, it is a single task called `localpro`. 
But if there are multiple ingreass tasks, you have to put all of them by separating them by a `:`.

### Step 4 (Setup APP Folder)
You need to make sure that you have a `APP_folder` with all the task specific files
inside the `task_specific_files` folder. 
The `APP_folder` needs to have a configuration.txt and a DAG_Scheduler.txt
The configuration.txt is used by CIRCE while the DAG_Scheduler.txt is used by WAVE.
**We are currently working on merging these two files.** 
The `APP_folder` MUST also contain all executable files of the task graph
under the `scripts` sub-folder. 
You need to follow this exact folder structure to develop an APP for 
the Jupiter Orchestrator.
**Detailed instructions for developing APPs for Jupiter will be posted later.**
```
    APP_folder
    |
    |   configuration.txt
    |   DAG_Scheduler.txt   
    |
    └───scripts
    |
    └───sample_input
        
```
### Step 5 (Setup the Dockers)
Now you need to update the `worker_node.Dockerfile` to add your app specific
packages as well as change the following line to refer to your app: `ADD
task_specific_files/network_monitoring_app/scripts/ /centralized_scheduler/`.
The dockerfiles can be found under the `circe/` folder.

### Step 6 (Push the Dockers)

Now, you need to build your Docker images. 
There are currently six different docker images with two each for the profiler, wave, and circe.

To build Docker images and push them to the Docker Hub repo, first login 
to Docker Hub using your own credentials by running `docker login`. Then, in the
folder with the *.Dockerfile files, use this template to build all the needed
Docker images:

    docker build -f $target_dockerfile . -t $dockerhub_user/$repo_name:$tag
    docker push $dockerhub_user/$repo_name:$tag

Example:

    docker build -f worker_node.Dockerfile . -t johndoe/worker_node:v1
    docker push johndoe/worker_node:v1
    docker build -f home_node.Dockerfile . -t johndoe/home_node:v1
    docker push johndoe/home_node:v1

The same thing needs to be done for the profiles and the WAVE files.

**To simplify the process we have provided with the following scripts:**
    
    scripts/build_push_jupiter.py --- push all Jupiter related dockers
    scripts/build_push_circe.py --- Push CIRCE dockers only
    scripts/build push_profiler.py --- Push DRUPE dockers only
    scripts/build_push_wave.py --- Push WAVE dockers only

**However, before running any of these four script you should update the `jupiter_config `file
with your own docker names as well as dockerhub username. 
DO NOT run the script without crosschecking the config file.**

### Step 7 (Setup the Proxy)
Now, you have to create a kubernetes proxy. You can do that by running the follwing command on a terminal.

    kubectl proxy -p 8080


### Step 8 (Create the Namespaces)
You need to create three difference namespaces in your Kubernetes cluster 
that will be dedicated to the profiler, WAVE, and CIRCE deployments, respectively.
You can create these namespaces commands similar to the following:
```
     kubectl create namespace johndoe-circe
     kubectl create namespace johndoe-profiler
     kubectl create namespace johndoe-wave
```
**You also need to change the respective lines in the `jupiter_config.py` file.**
```
    DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
    PROFILER_NAMESPACE      = 'johndoe-profiler'
    WAVE_NAMESPACE          = 'johndoe-wave'

```
### Step 9 (Run the Jupiter Orchestrator)
Next, you can simply run:

    cd scripts/
    python3 k8s_jupiter_deploy.py

### Step 9 (Alternate)

If you do not want to use WAVE for the scheduler and design your own, you can do that by simply using the `static_assignment.py` and changing the `static_mapping` flag to `True`. 
To that you have to pipe your scheduling output to the static_assignment.py while conforming to the sample dag and sample schedule structure. Then you can run,

    cd scripts/
    python3 k8s_jupiter_deploy.py

### Step 10 (Interact With the DAG)

Now you can interact with the pos using the kubernetes dashboard. 
To access it just pen up a browser on your local machine and go to 
`http://127.0.0.1:8080/ui`. You should see the k8s dashboard. 
Hit `Ctrl+c` on the terminal running the server to turn off the proxy. 




## Teardown

To teardown the DAG deployment, run the following:
    
    python3 k8s_jupiter_teardown.py

Once the deployment is torn down, you can simply start from the begining of 
these instructions to make changes to your code and redeploy the DAG.


# Project Structure

The directory structure of the project MUST conform with the following:
```
Jupiter/
├── jupiter_config.py
├── k8_requirements.txt
├── LICENSE.txt
├── nodes.txt
├── ...
|
├── circe
│   ├── home_node.Dockerfile
│   ├── monitor.py
│   ├── readconfig.py
│   ├── requirements.txt
│   ├── rt_profiler_data_update.py
│   ├── rt_profiler_update_mongo.py
│   ├── runSQuery.py
│   ├── runtime_profiler_mongodb
│   ├── scheduler.py
│   ├── start_home.sh
│   ├── start_worker.sh
│   └── worker_node.Dockerfile
|
└── wave
|   ├── home
|   │   ├── Dockerfile
|   │   ├── input_node.txt
|   │   ├── master.py
|   │   └── start.sh
|   └── worker
|       ├── child_appointment.py
|       ├── Dockerfile
|       ├── requirements.txt
|       └── start.sh
|
├── profilers
│   ├── central
│   │   ├── central_input
│   │   │   ├── link_list.txt
│   │   │   └── nodes.txt
│   │   ├── central_mongod
│   │   ├── central_query_statistics.py
│   │   ├── central_scheduler.py
│   │   ├── Dockerfile
│   │   ├── generate_link_list.py
│   │   ├── requirements.txt
│   │   ├── resource_profiling_files
│   │   │   ├── insert_to_container.py
│   │   │   ├── ip_path
│   │   │   ├── job.py
│   │   │   └── read_info.py
│   │   └── start.sh
│   └── droplet
│       ├── automate_droplet.py
│       ├── Dockerfile
│       ├── droplet_generate_random_files
│       ├── droplet_mongod
│       ├── droplet_scp_time_transfer
│       ├── requirements.txt
│       ├── resource_profiler.py
│       └── start.sh
|
├── task_specific_files
│   └── APP_Folder
│       ├── configuration.txt
│       ├── DAG_Scheduler.txt
│       ├── sample_input
│       │   ├── sample1
│       │   └── sample2
│       └── scripts
│           ├── task1.py
│           └── task2.py
|
└── scripts
    ├── build_push_circe.py
    ├── build_push_jupiter.py
    ├── build_push_profiler.py
    ├── build_push_wave.py
    ├── delete_all_circe_deployments.py
    ├── delete_all_profilers.py
    ├── delete_all_waves.py
    ├── k8s_circe_scheduler.py
    ├── k8s_jupiter_deploy.py
    ├── k8s_jupiter_teardown.py
    ├── k8s_profiler_scheduler.py
    ├── k8s_wave_scheduler.py
    ├── static_assignment.py
    ├── write_deployment_specs.py
    ├── write_home_specs.py
    ├── write_profiler_service_specs.py
    ├── write_profiler_specs.py
    ├── write_service_specs.py
    ├── write_wave_service_specs.py
    └── write_wave_specs.py

```


# References
[1] Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari, “End-to-End Network Performance Monitoring for Dispersed Computing“, International Conference on Computing, Networking and Communications, March 2018

[2] Aleksandra Knezevic, Quynh Nguyen, Jason A. Tran, Pradipta Ghosh, Pranav Sakulkar, Bhaskar Krishnamachari, and Murali Annavaram, “DEMO: CIRCE – A runtime scheduler for DAG-based dispersed computing,” The Second ACM/IEEE Symposium on Edge Computing (SEC) 2017. (poster)

[3] Pranav Sakulkar, Pradipta Ghosh, Aleksandra Knezevic, Jiatong Wang, Quynh Nguyen, Jason Tran, H.V. Krishna Giri Narra, Zhifeng Lin, Songze Li, Ming Yu, Bhaskar Krishnamachari, Salman Avestimehr, and Murali Annavaram, “WAVE: A Distributed Scheduling Framework for Dispersed Computing“, USC ANRG Technical Report, ANRG-2018-01.

# Troubleshooting
While running the system for the first time, there might be a case that
CIRCE is not launched. That happens because the WAVE does not reply with the mapping.
This is due to the current design of WAVE where the WAVE home needs to run only after all
the WAVE worker have  booted up. 
Currently, Jupiter handles it using a static delay between the worker and master deployments.
Thus, due to random docker download time, during the first deploy some workers boot up
after the master has boot up. This causes a race condition that results in the failure of WAVE.
A better safeguarding against such situation is part of our plan for next release. 
If this happens (CIRCE is not launched within approximately 10 min), 
just teardown the whole deployment and redeploy. It should work fine.

# Acknowledgment
This material is based upon work supported by Defense Advanced Research Projects Agency (DARPA) under Contract No. HR001117C0053. Any views, opinions, and/or findings expressed are those of the author(s) and should not be interpreted as representing the official views or policies of the Department of Defense or the U.S. Government.
