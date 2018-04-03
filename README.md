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
        |       |   DAG_Scheduler.txt  
        |       |   app_config.ini 
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
inside the `app_specific_files` folder. 
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
    |   app_config.ini   
    |
    └───scripts
    |
    └───sample_input
        
```
### Step 5 (Setup the Dockerfiles)
The circe dockerfiles can be found under the `circe/` folder.

Change the follwing lines in the `home_node.Dockerfile` to refer to your own app
```
# Add input files
COPY  app_specific_files/network_monitoring_app/sample_input /sample_input
```
```
# Add the task speficific configuration files
ADD app_specific_files/network_monitoring_app/configuration.txt /configuration.txt
```

Now you need to update the `worker_node.Dockerfile` to add your app specific
packages by changing the follwing lines:
```
## Install TASK specific needs. The hadoop is a requirement for the network profiler application
RUN wget http://supergsego.com/apache/hadoop/common/hadoop-2.8.1/hadoop-2.8.1.tar.gz -P ~/
RUN tar -zxvf ~/hadoop-2.8.1.tar.gz -C ~/

```
Also change the following line to refer to your app: 
```
ADD app_specific_files/network_monitoring_app/scripts/ /centralized_scheduler/
```


To simplify the process of customizing dockers, we have also provided with two functions in `circe_docker_files_generator.py` that generates the user customized dockers


Similarly there are docker files for the profilers and the mapper. 
For all the dockers, we have provided respective functions to automate the dockerfile generation and easier customizations.

### Step 6 (Choose the Task Mapper)

Next, you choose which mapper to choose from the three available options: HEFT (0), WAVE_random (1), and WAVE Greedy (2). This can be done by chaning the value assigned to the `SCHEDULER` in the `jupiter_config.ini` file

    [CONFIG]
        SCHEDULER = 2

The values to choose between the options are also listed in that file as 

    [SCHEDULER_LIST]
        HEFT = 0
        WAVE_RANDOM = 1
        WAVE_GREEDY = 2


### Step 7 (Push the Dockers)

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
    scripts/build_push_heft.py --- Push HEFT dockers only


**However, before running any of these four script you should update the `jupiter_config `file
with your own docker names as well as dockerhub username. 
DO NOT run the script without crosschecking the config file.**

### Step 8 (Setup the Proxy)
Now, you have to create a kubernetes proxy. You can do that by running the follwing command on a terminal.

    kubectl proxy -p 8080


### Step 9 (Create the Namespaces)
You need to create three difference namespaces in your Kubernetes cluster 
that will be dedicated to the network and resourse profilers (aka profilers), Execution Profilers (aka exec), WAVE, and CIRCE deployments, respectively.
You can create these namespaces commands similar to the following:
```
     kubectl create namespace johndoe-circe
     kubectl create namespace johndoe-profiler
     kubectl create namespace johndoe-mapper
     kubectl create namespace johndoe-exec

```
**You also need to change the respective lines in the `jupiter_config.py` file.**
```
    DEPLOYMENT_NAMESPACE    = 'johndoe-circe'
    PROFILER_NAMESPACE      = 'johndoe-profiler'
    MAPPER_NAMESPACE        = 'johndoe-mapper'
    EXEC_NAMESPACE          = 'johndoe-exec'

```



### Step 10 (Run the Jupiter Orchestrator)
Next, you can simply run:

    cd scripts/
    python3 k8s_jupiter_deploy.py

### Step 10 (Alternate)

If you do not want to use MAPPER and run your own custom mapping, you can do that by simply using the `static_assignment.py` and making `STATIC_MAPPING = 1` in the follwing line of the `jupiter_config.ini`

    [CONFIG]
        STATIC_MAPPING = 0 
Now, you have to pipe your scheduling output to the static_assignment.py while conforming to the sample dag and sample schedule structure. Then you can run,

    cd scripts/
    python3 k8s_jupiter_deploy.py

### Step 11 (Interact With the DAG)

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
├── jupiter_config.ini
├── jupiter_config.py
├── k8_requirements.txt
├── LICENSE.txt
├── nodes.txt
├── README.md
├── sourceit.sh
|
├── app_specific_files
│   └── network_monitoring_app
│       ├── app_config.ini
│       ├── configuration.txt
│       ├── ...
│       ├── input_node.txt
│       ├── LICENSE.txt
│       ├── README.md
│       ├── sample_input
│       │   ├── 1botnet.ipsum
│       │   └── 2botnet.ipsum
│       └── scripts
│           ├── ...
│           └── ...
├── circe
│   ├── circe_docker_files_generator.py
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
├── docs
│   ├── make.bat
│   ├── Makefile
│   └── source
│       ├── conf.py
│       └── index.rst
├── profilers
│   ├── execution_profiler
│   │   ├── central_mongod
│   │   ├── exec_docker_files_generator.py
│   │   ├── exec_home.Dockerfile
│   │   ├── exec_worker.Dockerfile
│   │   ├── get_files.py
│   │   ├── keep_alive.py
│   │   ├── profiler_home.py
│   │   ├── profiler_worker.py
│   │   ├── requirements.txt
│   │   ├── start_home.sh
│   │   └── start_worker.sh
│   └── network_resource_profiler
│       ├── home
│       │   ├── central_input
│       │   │   ├── link_list.txt
│       │   │   └── nodes.txt
│       │   ├── central_mongod
│       │   ├── central_query_statistics.py
│       │   ├── central_scheduler.py
│       │   ├── generate_link_list.py
│       │   ├── requirements.txt
│       │   ├── resource_profiling_files
│       │   │   ├── insert_to_container.py
│       │   │   ├── ip_path
│       │   │   ├── job.py
│       │   │   └── read_info.py
│       │   └── start.sh
│       ├── profiler_docker_files_generator.py
│       ├── profiler_home.Dockerfile
│       ├── profiler_worker.Dockerfile
│       └── worker
│           ├── automate_droplet.py
│           ├── droplet_generate_random_files
│           ├── droplet_mongod
│           ├── droplet_scp_time_transfer
│           ├── keep_alive.py
│           ├── requirements.txt
│           ├── resource_profiler.py
│           └── start.sh
├── task_mapper
|   ├── heft
|   │   ├── create_input.py
|   │   ├── heft.Dockerfile
|   │   ├── heft_dockerfile_generator.py
|   │   ├── heft_dup.py
|   │   ├── input_0.tgff
|   │   ├── keep_alive.py
|   │   ├── master.py
|   │   ├── read_input_heft.py
|   │   ├── requirements.txt
|   │   ├── start.sh
|   │   └── write_input_heft.py
|   └── wave
|       ├── greedy_wave
|       │   ├── home
|       │   │   ├── master.py
|       │   │   ├── requirements.txt
|       │   │   └── start.sh
|       │   ├── home.Dockerfile
|       │   ├── worker
|       │   │   ├── child_appointment.py
|       │   │   ├── requirements.txt
|       │   │   └── start.sh
|       │   └── worker.Dockerfile
|       └── random_wave
|           ├── home
|           │   ├── master.py
|           │   ├── requirements.txt
|           │   └── start.sh
|           ├── home.Dockerfile
|           ├── worker
|           │   ├── child_appointment.py
|           │   ├── requirements.txt
|           │   └── start.sh
|           └── worker.Dockerfile
└── scripts
    ├── build_push_circe.py
    ├── build_push_exec.py
    ├── build_push_heft.py
    ├── build_push_jupiter.py
    ├── build_push_profiler.py
    ├── build_push_wave.py
    ├── build_push_wave.pyc
    ├── delete_all_circe_deployments.py
    ├── delete_all_exec.py
    ├── delete_all_heft.py
    ├── delete_all_profilers.py
    ├── delete_all_waves.py
    ├── k8s_circe_scheduler.py
    ├── k8s_exec_scheduler.py
    ├── k8s_get_service_ips.py
    ├── k8s_heft_scheduler.py
    ├── k8s_jupiter_deploy.py
    ├── k8s_jupiter_teardown.py
    ├── k8s_profiler_scheduler.py
    ├── k8s_wave_scheduler.py
    ├── static_assignment.py
    ├── utilities.py
    ├── write_circe_service_specs.py
    ├── write_circe_specs.py
    ├── write_exec_service_specs.py
    ├── write_exec_specs.py
    ├── write_heft_service_specs.py
    ├── write_heft_specs.py
    ├── write_profiler_service_specs.py
    ├── write_profiler_specs.py
    ├── write_wave_service_specs.py
    └── write_wave_specs.py

```

# Visualization
The visualization tool for Jupiter is given [here](https://github.com/ANRGUSC/Jupiter_Visualization ). This tool generates an interactive plot to show the scheduling result of WAVE and the dispatcher mapping of CIRCE. To visualize your own application, make sure the format of your logs are in line with the input files of the tools. We will integrate this as a real-time visualization tool for Jupiter in the next release.  

# References
[1] Quynh Nguyen, Pradipta Ghosh, and Bhaskar Krishnamachari, “End-to-End Network Performance Monitoring for Dispersed Computing“, International Conference on Computing, Networking and Communications, March 2018

[2] Aleksandra Knezevic, Quynh Nguyen, Jason A. Tran, Pradipta Ghosh, Pranav Sakulkar, Bhaskar Krishnamachari, and Murali Annavaram, “DEMO: CIRCE – A runtime scheduler for DAG-based dispersed computing,” The Second ACM/IEEE Symposium on Edge Computing (SEC) 2017. (poster)

[3] Pranav Sakulkar, Pradipta Ghosh, Aleksandra Knezevic, Jiatong Wang, Quynh Nguyen, Jason Tran, H.V. Krishna Giri Narra, Zhifeng Lin, Songze Li, Ming Yu, Bhaskar Krishnamachari, Salman Avestimehr, and Murali Annavaram, “WAVE: A Distributed Scheduling Framework for Dispersed Computing“, USC ANRG Technical Report, ANRG-2018-01.

# Troubleshooting
You will notice that some times the jupiter deploy script says that certain pods are not running. If some pods persist in the list for a long time, it is advisable to look into the k8 dashboard to check whether the pod is on a CrashLoopBack state. If yes, you can just delete the pod using the dropdown menu in the dashboard. **DO NOT Delete Anything but the pod i.e. DO NOT delete the SVC, Deployment or the Recplicaset.** By doing this, the k8 will spawn a new instance of the pod. If the problem persists, look at the logs or the error message for more details.

# Acknowledgment
This material is based upon work supported by Defense Advanced Research Projects Agency (DARPA) under Contract No. HR001117C0053. Any views, opinions, and/or findings expressed are those of the author(s) and should not be interpreted as representing the official views or policies of the Department of Defense or the U.S. Government.
