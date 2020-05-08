"""
In file cal_duplication, we choose a node and a set of tasks to duplicate on this node
This file takes the node name and tasks as input, does task graph and mapping change

- What this program does:
    1. Create K new tasks (tasks that transfer data through btnk link), map them on the selected node
    2. Add the K tasks as new child for all the parent tasks
    3. Remove the parent-child relations between tasks that communicate through btnk link
    
- Prerequisites knowledge:
    1. The mapper pod is exposed as a service where an instance of flask is running in container.
       The flask can be queried through kube proxy and return assignment, which is a hashmap like
       {"task0": "node2", "task1": "node1", "task2": "node1", "task3": "node1"}
    2. File auto_deploy_system reads configuration and node file, passes them to mapper, gets "dag" and "schedule", then CIRCE
    3. File k8s_circe_scheduler.py creates all CIRCE pods (services, deployments, replicasets). Each pod is injected
       with a env variable called CHILD_NODES, which is a pod where the child tasks run. It task node.txt and configuration.txt from 
       CIRCE home container, which are copied from code folder
    4. Each CIRCE instance has fs monitor for its input folder, wait for number of files then start processing; also fs monitor for 
       output folder, where it scp files to child input folder. Children are unaware of parents

- How to do it:
    We have to change both tasks and mapping, but CIRCE is hard-coded so that it iterates through DAG and creates a pod for each task
    For duplication, we'll create another pod which runs exactly the same task. The DAG updated by mappers can't modify the original 
    configuration file that CIRCE takes input from. In order to make minimum changes, we pass the new DAG, together with the 'assignment'
    to CIRCE through flask and kube service. For new tasks, we have to use new names, but refer to old tasks.

    Maintain all the data (task list, comp matrix etc) in the heft_dup file.

"""
class Duplicate:
    
    def __init__(self, links, processors, tasks, comp_cost, data, quaratic_profile, btnk_id, idle_proc):
    
    def get_dag_from_file(self):
    
    def write_dag_to_file(self):
