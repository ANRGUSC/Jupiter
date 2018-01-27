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
```


## Deploy Instructions:

1) Clone/pull this repo and `cd` into the repo's directory. 

2) You need to make sure that you have a updated nodes.txt file with a list of nodes from your cluster.

3) You need to make sure that you have a folder with all the task specific files inside the `task_specific_files` folder. The task specific folder needs to have a configuration.txt. Also under that folder, you need to have all executable files of the task graph under the scripts folder. You need to follow this exact folder structure to use the Jupiter Orchestrator. 

4) Now you need to update the `worker_node.Dockerfile` to add your app specific packages as well as change the follwing line to refer to your app: `ADD task_specific_files/network_monitoring_app/scripts/ /centralized_scheduler/`

5) Now, you need to build your Docker images. There are currently two separate images: the "home_node" image and 
"worker_node" image.

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
To simplify the process we have provided with the following scripts:
    
    build_push_jupiter.py --- push all Jupiter related dockers
    build_push_circe.py --- Push CIRCE dockers only
    build push_profiler.py --- Push DRUPE dockers only
    build_push_wave.py --- Push WAVE dockers only

However, before running any of these four script you should update the `jupiter_config `file
with your own docker names. DO NOT run the script without crosschecking the config file.

6) Note: If you just want to control the whole cluster via our master node (i.e. you don't
want to use your computer) go to [this section](#controlling-cluster-from-k8s-master-node) 
in the readme).

To control the cluster, you need to grab the `admin.conf` file from the k8s 
master node. When the cluster is bootstrapped by `kubeadm` [see the k8s cluster
setup notes here](https://drive.google.com/open?id=1NeewrSx9Bp3oNOGGpgyfKBjul1NbSB8kHqy7gslxtKk)
the `admin.conf` file is stored in `/etc/kubernetes/admin.conf`. Usually, a copy
is made into the $HOME folder. Either way, make a copy of `admin.conf` into your 
local machine's home folder. Then, make sure you have `kubectl` installed ([instrcutions 
here](https://kubernetes.io/docs/tasks/tools/install-kubectl/)). Next, you need 
to run the commands below. You can wrap it up in a script you source or directly 
place the export line and source line into your .bashrc file. However, make sure 
to re-run the full set of commands if the `admin.conf` file has changed:

    sudo chown $(id -u):$(id -g) $HOME/admin.conf
    export KUBECONFIG=$HOME/admin.conf #check if it works with `kubectl get nodes`
    source <(kubectl completion bash)

Currently, you need to have
`admin.conf` in the $Home folder. Our python scripts need it exactly
there to work. 

7) Now, you have to create a kubernetes proxy. You can do that by running the follwing command on a terminal.

    ```kubectl proxy -p 8080```

8) Next, you can simply run:

   ```python3 k8s_jupiter_deploy.py```


9) Now you can interact with the pos using the kubernetes dashboard. 
To access it just pen up a browser on your local machine and go to 
`http://127.0.0.1:8080/ui`. You should see the k8s dashboard. Hit `Ctrl+c` on
the terminal running the server to turn off the proxy. 

## Teardown

To teardown the DAG deployment, run the following:
    
    python3 k8s_jupiter_teardown.py

Once the deployment is torn down, you can simply start from the begining of 
these instructions to make changes to your code and redeploy the DAG.

