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

import heft_dup as hd
import numpy as np
import time

class Split:

    # NOTE: for now assume this only happens when the bottleneck is a node
    def do_split(self, links, processors, tasks, comp_cost, data, quaratic_profile, btnk_id):
        """
        iterate through all the idle nodes, try duplicating all tasks on this node
        calculate the maximum of incurred link and node usage, use it as "cost" of this node
        select an idle node with minimum cost
        """
        """
        update node and link usage and task processors
        a task with more than one processor implies that it is a splitted task
        this will show up in the task.extra_proc_nums
        """    
        # ---------------------------------- part1: find best node and portion ----------------------------------------
        btnk_node = self.get_node_by_id(processors, btnk_id)
        btnk_time = btnk_node.time_line[-1].end
        print("current bottleneck number  " + str(btnk_node.number))
        
        # get all link usage related to this node, including all parent and child node links with this node
        # {parent nodes ids -> list of file transfer size to this node from parents}
        parent_nodes_files = {}
        # {child nodes ids -> list of file transfer size to child from this node}
        child_nodes_files = {}
        task_ids_to_dup = [] # tasks on this node
        for dur in btnk_node.time_line:
            task_ids_to_dup.append(dur.task_num)
        
        for tid in task_ids_to_dup:
            for pn in tasks[tid].parents_numbers:
                proc_num = self.get_node_by_id(processors, pn).number
                if not proc_num in parent_nodes_files:
                    parent_nodes_files[proc_num] = []
                parent_nodes_files[proc_num].append(data[pn][tid])
        for tid in task_ids_to_dup:
            for child_id in range(len(tasks)):
                if data[tid][child_id] > 0:
                    proc_num = self.get_node_by_id(processors, child_id).number
                    if not proc_num in child_nodes_files:
                        child_nodes_files[proc_num] = []
                    child_nodes_files[proc_num].append(data[tid][child_id])
                    
        procid_to_max_time = {}
        for proc in processors:
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
            # edge case: task to split has no parent or has no child
            max_comm_cost = 0
            if len(new_transfer_times) > 0:
                max_comm_cost = max(max_comm_cost, max(new_transfer_times.values()))

            max_comp_cost = 0.0
            for tid in task_ids_to_dup:
                max_comp_cost += comp_cost[tid][proc.number]
            procid_to_max_time[proc.number] = max(max_comp_cost, max_comm_cost)
        
        if len(procid_to_max_time) == 0:
            return False    
        print("procid to max time in split")
        print(procid_to_max_time)
        # pick a node that minimizes the max extra cost incurred
        best_node_id = -1
        min_btnk_val = time.time() # infinity time value
        for procid in procid_to_max_time:
            if procid_to_max_time[procid] < min_btnk_val:
                min_btnk_val = procid_to_max_time[procid]
                best_node_id = procid
        print("replicate btnk node on  " + str(best_node_id))
        # here we need to cover both cases: current btnk node is an intact node, or an alrealy splitted node
        # the portion here refers to the global portion of the original task
        # i.e. if cur btnk node portion is 0.5, then new split can result in 0.25, 0.25
        cur_portion = 1.0
        rand_task = tasks[btnk_node.time_line[0].task_num]
        if len(rand_task.proc_num_to_portion) > 0: 
            cur_portion = rand_task.proc_num_to_portion[btnk_node.number]
        
        new_node_portion = float(min_btnk_val) / (float(min_btnk_val) + float(btnk_time))
        original_node_portion = 1.0 - new_node_portion
        new_node = self.get_node_by_id(processors, best_node_id)
        
        # ---------------------------------- part2: do split ----------------------------------------
        # for ALL links inbound and outbound to btnk_node, takeup_time *= original_node_portion
        # same for new node
        # NOTE: the bottleneck node could be one that's already a split version 
        for link in links:
            # if this node is the outbound
            if link.id.split('_')[0] == str(btnk_node.number):
                dup_link = self.get_link_by_id(links, str(new_node.number)+'_'+str(link.id.split('_')[1]))
                for lkdur in link.time_line:
                    new_lkdur = hd.LinkDuration(lkdur.start_task_num, lkdur.end_task_num, lkdur.start*new_node_portion, lkdur.end*new_node_portion)
                    lkdur.start *= original_node_portion
                    lkdur.end *= original_node_portion
                    dup_link.time_line.append(new_lkdur)
            elif link.id.split('_')[1] == str(btnk_node.number):
                dup_link = self.get_link_by_id(links, str(link.id.split('_')[0])+'_'+str(new_node.number))
                for lkdur in link.time_line:
                    new_lkdur = hd.LinkDuration(lkdur.start_task_num, lkdur.end_task_num, lkdur.start*new_node_portion, lkdur.end*new_node_portion)
                    lkdur.start *= original_node_portion
                    lkdur.end *= original_node_portion
                    dup_link.time_line.append(new_lkdur)
                    
        for dur in btnk_node.time_line:
            new_dur = hd.Duration(dur.task_num, dur.start*new_node_portion, dur.end*new_node_portion)
            dur.start *= original_node_portion
            dur.end *= original_node_portion
            new_node.time_line.append(new_dur)
        
        for tid in task_ids_to_dup:
            tasks[tid].proc_num_to_portion[btnk_node.number] = cur_portion * original_node_portion
            tasks[tid].proc_num_to_portion[new_node.number] = cur_portion * new_node_portion
        
        return True
        
    def get_link_by_id(self, links, link_id):
        for link in links:
            if link.id == link_id:
                return link
    
    def get_node_by_id(self, processors, node_id):
        return processors[int(node_id)]
        
    def cal_comm_quadratic(self, file_size, quaratic_profile):
        return (np.square(file_size)*quaratic_profile[0] + file_size*quaratic_profile[1] + quaratic_profile[2]) 
