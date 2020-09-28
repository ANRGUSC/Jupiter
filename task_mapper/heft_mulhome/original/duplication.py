"""
----------------------------- part1: calculate duplication ----------------------------
The condition under which duplication can improve the throughput: 
possible new bottlenecks introduced in the system are less than the old one. 


Possible new bottlenecks include:

1. Copy tasks (which transfer data using bottleneck link) from src node to idle node. Don't copy all src node tasks.
   The new execution time sum of those copied tasks on the idle node cannot exceed the bottleneck time.
2. Find all nodes who has a parent task of any of the copied tasks. Since we use virtual links, 
   the links related to a new node are all idle, thus we just need to make sure 
   the new file transfer time on each link is less than the bottleneck.
3. Transfer time from new node to dst node is less than bottleneck.

----------------------------- part2: duplicate ----------------------------------------

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

"""
    this class has two main functions, namely "get_dup_node" and "duplicate"
    all the data-structures are passed into these functions by reference from file heft_dup
    this class doesn't maintain any instance level data-structures
"""
import numpy as np
import heft_dup as hd
import time

class Duplication:

    def get_dup_node(self, links, processors, tasks, comp_cost, data, quaratic_profile, btnk_id):
        """
        input: links and nodes, and the bottleneck link to bypass
        calculate a hashmap of candidate nodes and the max value of incurred resource takeup time
        output: best candidate node
        """
        btnk_link = self.get_link_by_id(links, btnk_id)
        btnk_time = btnk_link.time_line[-1].end
        src_proc = self.get_proc_by_id(processors, btnk_id.split('_')[0])
        dst_proc = self.get_proc_by_id(processors, btnk_id.split('_')[1])
        
        # hashmap { task number (index in the tasks list) -> processor id }
        task_to_proc = self.get_procs_by_tasks(processors)
        
        # get tasks in src proc that transfer file to dst proc
        # get tasks in dst proc that receive file from src node
        # dup[i] -> recv[i] represents a pair of file transfer
        # currently we're not using advanced multicast, so same file can take twice the time to transfer to two destinations
        task_ids_to_dup = []
        task_ids_to_recv = []
        for linkdur in btnk_link.time_line:
            task_ids_to_dup.append(linkdur.start_task_num)
            task_ids_to_recv.append(linkdur.end_task_num)
        
        # find all parents of the to-be-duplicated tasks
        parent_tasks = set()
        for parent in tasks:
            for task_id in task_ids_to_dup:
                if data[parent.number][task_id] > 0:
                    parent_tasks.add(parent)
        
        # a list of file sizes to transfer from idle node to dst node
        # these are fixed on two nodes      
        files_to_dst = [] 
        # node id -> list of file sizes to transfer to idle node
        # fixed destination node but multiple source nodes
        files_from_src = {} 
        for i in range(len(task_ids_to_dup)):
            files_to_dst.append(data[task_ids_to_dup[i]][task_ids_to_recv[i]])
        for task_src in parent_tasks:
            for tid_dst in task_ids_to_dup:
                if data[task_src.number][tid_dst] > 0:
                    src_proc = task_to_proc[task_src.number]
                    if not src_proc in files_from_src:
                        files_from_src[src_proc] = []
                    files_from_src[src_proc].append(data[task_src.number][tid_dst])
                    
        print("task ids to dup, task ids to recv, files_to_dst, files_from_src")
        print(task_ids_to_dup)
        print(task_ids_to_recv)
        print(files_to_dst)
        print(files_from_src)
        # hashmap {idle node id to duplicate : max new time incurred}. New incurred times:
        # 1. all parent nodes to idle node link usage
        # 2. idle node computation
        # 3. idle node to destination node transfer
        procid_to_max_time = {}
        for proc in processors:
            if len(proc.time_line) != 0:
                continue
            else: # this is an idle node
                # get sum of computation time
                comp_time = 0
                for task_id in task_ids_to_dup:
                    comp_time = comp_time + comp_cost[task_id][proc.number]
                
                # get the max of all link transfer time
                # new node to destination node
                time_to_dst = 0.0
                if len(files_to_dst) > 0:
                    for file_size in files_to_dst:
                        time_to_dst += self.cal_comm_quadratic(file_size, quaratic_profile[proc.number][dst_proc.number])
                        
                # all source nodes to new node
                time_from_src = []
                for nodeid in files_from_src:
                    key = processors[nodeid]
                    cur_time = 0.0
                    for file_size in files_from_src[key.number]:
                        cur_time += self.cal_comm_quadratic(file_size, quaratic_profile[key.number][proc.number])
                    time_from_src.append(cur_time)
                    
                # corner case: src node has no parent or dst node has no child
                new_btnk_proc = 0
                if len(time_from_src) > 0:
                    new_btnk_proc = max(time_from_src)
                new_btnk_proc = max(new_btnk_proc, time_to_dst)
                new_btnk_proc = max(new_btnk_proc, comp_time)
                procid_to_max_time[proc.number] = new_btnk_proc
                
        print("procid to max time")
        print(procid_to_max_time)
        min_btnk = time.time()
        nodeid = -1
        for key in procid_to_max_time:
            if procid_to_max_time[key] < min_btnk:
                min_btnk = procid_to_max_time[key]
                nodeid = key
        print("chosen node id, min btnk, task ids to dup, tak ids to recv, parent tasks, files to dest, files from src")
        print(nodeid, min_btnk, task_ids_to_dup, task_ids_to_recv, [pt.number for pt in parent_tasks], files_to_dst, files_from_src)
        '''
        if min_btnk >= btnk_time: # no point for duplication
            nodeid = -1
        '''
        return (nodeid, min_btnk, task_ids_to_dup, task_ids_to_recv, list(parent_tasks), files_to_dst, files_from_src)
    
    
    def duplicate(self, links, processors, tasks, comp_cost, data, quaratic_profile, btnk_id, new_node,
                  min_btnk, task_ids_to_dup, task_ids_to_recv, parent_tasks, task_names, files_to_dst, files_from_src):
        """
        what to do in actual duplicate;
        1. update takeup times of related nodes and links, comp matrix etc
        2. read the configuration task file, override it with updated task graph
            2.1 name (create) duplicated tasks, add children
            2.2 remove children of original tasks
            2.3 add children to parent source tasks
        """
        tasks_to_dup = [self.get_task_by_number(tasks, i) for i in task_ids_to_dup]
        tasks_to_recv = [self.get_task_by_number(tasks, i) for i in task_ids_to_recv]
        src_proc = self.get_proc_by_id(processors, btnk_id.split('_')[0])
        dst_proc = self.get_proc_by_id(processors, btnk_id.split('_')[1])
        
        # a mapping from old task number to its dup task number and the other way around
        ori_to_dup = {}
        dup_to_ori = {}
        # create tasks
        for task in tasks_to_dup:
            dup_task = hd.Task(-1)
            dup_task.number = len(tasks)
            ori_to_dup[task.number] = dup_task.number
            dup_to_ori[dup_task.number] = task.number
            dup_task.comp_cost = task.comp_cost
            dup_task.processor_num = new_node.number
            dup_task.parents_numbers = task.parents_numbers
            dup_task.up_rank = task.up_rank
            cur_end_time = new_node.time_line[-1].end if len(new_node.time_line) > 0 else 0
            dt = hd.Duration(dup_task.number, cur_end_time, cur_end_time + dup_task.comp_cost[new_node.number])
            new_node.time_line.append(dt)
            tasks.append(dup_task)
            comp_cost.append(dup_task.comp_cost)
            task_names.append(task_names[task.number]+"-dup")
            
        print("task numbers: ori to dup, dup to ori")
        print(ori_to_dup)
        print(dup_to_ori)
        # change parent child relations (src -> dst)
        for child in tasks_to_recv:
            for index in range(len(child.parents_numbers)):
                if child.parents_numbers[index] in task_ids_to_dup:
                    child.parents_numbers[index] = ori_to_dup[child.parents_numbers[index]]
        print("original data matrix")
        print(data)     
        # expand data transfer matrix
        l = [-1 for t in task_ids_to_dup]
        for row in range(len(data)):
            data[row] = data[row] + l
        while(len(l) < len(data[0])):
            l.append(-1)
        while(len(data) < len(data[0])):
            data.append(l)
                        
        # change parent-child data transfer
        for t in tasks_to_dup:
            for prnum in t.parents_numbers:
                data[prnum][ori_to_dup[t.number]] = data[prnum][t.number]
        for pid in task_ids_to_dup:
            for dr in dst_proc.time_line:
                if data[pid][dr.task_num] > 0:
                    data[ori_to_dup[pid]][dr.task_num] = data[pid][dr.task_num]
                    data[pid][dr.task_num] = -1
        print("updated data transfer matrix with task duplication")
        print(data)
        print("updated task names with dupicated tasks")
        print(task_names)
        # update link durations
        # NOTE: corner case here, the parent and child can be scheduled on the same node originally, but seperated after dup
        # thus causing a new link usage, so can't just copy original link usage
        """
        new_link = self.get_link_by_id(links, str(new_node.number)+'_'+str(dst_proc.number))
        old_link = self.get_link_by_id(links, btnk_id)
        for ld in old_link.time_line:
            new_link.time_line.append(hd.LinkDuration(ori_to_dup[ld.start_task_num], ld.end_task_num, ld.start, ld.end))
        old_link.time_line = [] # remove bottleneck link
        for pt in parent_tasks:
            print("old link, new link", str(pt.processor_num) + '_' + str(new_node.number), str(pt.processor_num) + '_' + str(src_proc.number))
            new_link = self.get_link_by_id(links, str(pt.processor_num) + '_' + str(new_node.number))
            old_link = self.get_link_by_id(links, str(pt.processor_num) + '_' + str(src_proc.number))
            for ld in old_link.time_line:
                if ld.end_task_num in task_ids_to_dup:
                    new_link.time_line.append(hd.LinkDuration(ld.start_task_num, ori_to_dup[ld.end_task_num], ld.start, ld.end))
        """
        # from selected new node to dst node: task_ids_to_dup[i] -> task_ids_to_recv[i]
        # from parents to selected nodes: files_from_src[nodeid]
        
        # link from new node to dst node
        if new_node.number != dst_proc.number:
            new_link = self.get_link_by_id(links, str(new_node.number)+'_'+str(dst_proc.number))
            if len(task_ids_to_dup) > 0:
                for idx in range(len(task_ids_to_dup)):
                    new_task = ori_to_dup[task_ids_to_dup[idx]]
                    file_size_to_tran = data[new_task][task_ids_to_recv[idx]]
                    start_time = 0 if len(new_link.time_line) == 0 else new_link.time_line[-1].end
                    transfer_time = self.cal_comm_quadratic(file_size_to_tran, quaratic_profile[new_node.number][dst_proc.number])
                    ld = hd.LinkDuration(new_task, task_ids_to_recv[idx], start_time, start_time + transfer_time)
                    new_link.time_line.append(ld)
            print("new_link to dst")
            print(new_link.id)
            if len(new_link.time_line) > 0:
                for tl in new_link.time_line:
                    print(tl.start_task_num, " ", tl.end_task_num, " ", tl.start, " ", tl.end)
        # maintain a data-structure: 
        # parent_ids, child_ids, file_sizes: parent[i] transfer file_size[i] to child[i]
        parent_ids = []
        child_ids = []
        file_sizes = []
        for pt in parent_tasks:
            for ctid in task_ids_to_dup:
                if data[pt.number][ctid] > 0:
                    parent_ids.append(pt.number)
                    child_ids.append(ctid)
                    file_sizes.append(data[pt.number][ctid])
        if len(file_sizes) > 0:
            procnum = self.get_task_by_number(tasks, parent_ids[idx]).processor_num
            for idx in range(len(file_sizes)):
                if procnum != new_node.number:
                    new_link = self.get_link_by_id(links, str(procnum)+'_'+str(new_node.number))
                    start_time = 0 if len(new_link.time_line) == 0 else new_link.time_line[-1].end
                    tran_time = self.cal_comm_quadratic(file_sizes[idx], quaratic_profile[procnum][new_node.number])
                    ld = hd.LinkDuration(parent_ids[idx], ori_to_dup[child_ids[idx]], start_time, start_time + tran_time)
                    new_link.time_line.append(ld)
                    print("new_link from parents")
                    print(new_link.id)
                    if len(new_link.time_line) > 0:
                        for tl in new_link.time_line:
                            print(tl.start_task_num, " ", tl.end_task_num, " ", tl.start, " ", tl.end)
        print('\n\n')
        path = 'dag.txt'
        self.rewrite_graph_file(path, data, task_names)
        return True
    
    
    def get_link_by_id(self, links, link_id):
        for link in links:
            if link.id == link_id:
                return link

    def get_task_by_number(self, tasks, task_num):
        for tk in tasks:
            if tk.number == task_num:
                return tk
      
    def get_proc_by_id(self, processors, proc_id):
        return processors[int(proc_id)]    
    
                
    def get_procs_by_tasks(self, processors):
        task_to_proc = {}
        for proc in processors:
            if len(proc.time_line) == 0:
                continue
            else:
                for duration in proc.time_line:
                    task_to_proc[duration.task_num] = proc.number
        return task_to_proc
    
            
    def cal_comm_quadratic(self, file_size, quaratic_profile):
        return (np.square(file_size)*quaratic_profile[0] + file_size*quaratic_profile[1] + quaratic_profile[2]) 
    
    
    def construct_graph(self, data):
        
        size = len(data)
        adjList = [[] for n in range(size)]
        for parent in range(size):
            for child in range(size):
                if data[parent][child] > 0:
                    adjList[parent].append(child)
        return adjList
    
    
    def rewrite_graph_file(self, path, data, task_names):
        
        adjList = self.construct_graph(data)
        taskname_to_numinput = {}
        taskname_to_flag = {}
        # a set of tasks whose child tasks contain 'home' 
        exit_task_names = set()
        f = open(path, "r")
        """
        Example graph:
        4
        task0 1 true task1 task2
        task1 1 true task3
        task2 1 true task3
        task3 2 true home
        """
        line = f.readline().rstrip('\n')
        while(1):
            line = f.readline().rstrip('\n')
            if len(line) == 0:
                break
            info = line.split(' ')
            name = info[0]
            taskname_to_numinput[name] = info[1]
            taskname_to_flag[name] = info[2]
            if 'home' in info:
                exit_task_names.add(name)
        f.close()
        for name in task_names:
            if not name in taskname_to_flag:
                taskname_to_numinput[name] = taskname_to_numinput[name.split('-')[0]]
                taskname_to_flag[name] = taskname_to_flag[name.split('-')[0]]
        f = open(path, "w")
        f.write(str(len(data))+'\n')
        for tid in range(len(adjList)):
            tname = task_names[tid]
            newline =  tname + " " + taskname_to_numinput[tname] + " " + taskname_to_flag[tname]
            for cid in adjList[tid]:
                newline = newline + " " + task_names[cid]
            if tname in exit_task_names:
                newline = newline + " " + "home"
            newline += '\n'
            f.write(newline)
        f.close()
