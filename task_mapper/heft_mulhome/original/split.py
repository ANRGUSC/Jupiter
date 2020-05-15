"""
duplication and split can both remove link bottlenecks, but only split can remove comp btnk
duplication is doing some tasks twice, and incurred multiple link usage to make btnk link completely idle
split can evenly distribute jobs on more reources without redundent work
duplication can be used when completely removal of a link is prefered
Some points:
1. the new node should duplicate all (not some) tasks assigned to original node
2. a node can have as many dup nodes, which will indefinately increase throughput
3. should set a bound on max number of idle nodes to use, can use two for now (consider idle node numbers)
4. how to calculate the portion of each nodes' work? 
     old node/links drop below btnk (it will always drop though, as long as portion < 1, because it is the btnk)
     new node/links don't become btnk. a simple way is to calculate the btnk of the par->cur->child path,
     and the par->new->child path, and assign portions so as to make them the same

Since any node can remove bottleneck, how to decide which node to split on?
Can choose a node that, after above calculation, reduces the bottleneck most (i.e. min new bottleneck)
"""

class Split:

    # NOTE: for now assume this only happens when the bottleneck is a node
    def get_split_node(self, links, processors, tasks, comp_cost, data, quaratic_profile, btnk_id):
        """
        iterate through all the idle nodes, try duplicating all tasks on this node
        calculate the maximum of incurred link and node usage, use it as "cost" of this node
        select an idle node with minimum cost
        """
        btnk_node = self.get_node_by_id(processors, btnk_id)
        btnk_time = btnk_node.time_line[-1].end
        
        # get all link usage related to this node, including all parent and child node links with this node
        # {parent nodes ids -> list of file transfer size to this node from parents}
        parent_nodes_files = {}
        # {child nodes ids -> list of file transfer size to child from this node}
        child_nodes_files = {}
        task_ids_to_dup = [] # tasks on this node
        for dur in btnk_node:
            task_ids_to_dup.append(dur.task_num)
        
        for tid in task_ids_to_dup:
            for pn in tasks[tid].parents_numbers:
                proc_num = self.get_node_by_id(processors, pn).processor_num
                if not proc_num in parent_nodes_files:
                    parent_nodes_files[proc_num] = []
                parent_nodes_files[proc_num].append(data[pn][tid])
        for tid in task_ids_to_dup:
            for child_id in range(len(tasks)):
                if data[tid][child_id] > 0:
                    proc_num = self.get_node_by_id(processors, child_id).processor_num
                    if not proc_num in child_node_files:
                        child_nodes_files[proc_num] = []
                    child_nodes_files[proc_num].append(data[tid][child_id])
                    
        procid_to_max_time = {}
        for proc in self.processors:
            # only pick idle nodes
            if len(proc.time_line) > 0:
                continue
            # parent or child node id -> total file transfer time between P or C and new node
            # i.e. {new links -> its new transfer time}
            new_transfer_times = {}
            for pnid in parent_nodes_files:
                new_transfer_times[pnid] = 0
            for cnid in child_nodes_files:
                new_transfer_times[cnid] = 0
            for pnid in parent_nodes_files:
                for file_size in parent_nodes_files[pnid]:
                    new_transfer_times[pnid] += self.cal_comm_quadratic(file_size, quaratic_profile[pnid][proc.number])
            for cnid in child_nodes_files:
                for file_size in child_nodes_files[cnid]:
                    new_transfer_times[cnid] += self.cal_comm_quadratic(file_size, quaratic_profile[proc.number][cnid])
            max_comm_cost = max(parent_nodes_files.values())
            max_comm_cost = max(max_comm_time, max(child_nodes_files.values()))
            comp_cost = 0.0
            for tid in task_ids_to_dup:
                comp_time += comp_cost[proc.number][tid]
            procid_to_max_time[proc.number] = max(comp_cost, max_comm_cost)
            
        # pick a node that minimizes the max extra cost incurred
        best_node_id = -1
        min_btnk_val = time.time() # infinity time value
        for procid in procid_to_max_time:
            if procid_to_max_time[procid] < min_btnk_val:
                min_btnk_val = procid_to_max_time[procid]
                best_node_id = procid
        new_node_portion = float(min_btnk_val) / (float(min_btnk_val) + float(btnk_time))
        
        return (self.get_node_by_id(processors, best_node_id), new_node_portion)
    
    def do_split(self.links, self.processors, self.tasks, self.comp_cost, self.data, self.quaratic_profile, btnk_id):
        """
        update node and link usage, also task.processors
        a task with more than one processor implies that it is a splitted task
        this will show up in the task.extra_proc_nums
        """    
    
    def get_node_by_id(self, processors, node_id):
        return processors[node_id]
        
    def cal_comm_quadratic(self, file_size, quaratic_profile):
        return (np.square(file_size)*quaratic_profile[0] + file_size*quaratic_profile[1] + quaratic_profile[2]) 
