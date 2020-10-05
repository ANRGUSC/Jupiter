
"""
This module is a modified version of HEFT that's designed to improve the steady-state throughput, in general,
    this algorithm tries to balance the time across all resources. Detailed steps are as follows:

1. task initialize: average computation of a task over all processors
2. comm initialize: average communication time of taska -> taskb over all processors
3. calculate task uprank
4. define resources: nodes and links. Use virtual links for now. 
5. for task in decreasing order of uprank, assign it to a processor that minimizes the max of ALL resource takeup time 
   (including processors and links)

Assume we don't know the actual link topology and routing rules of the cluster, we can imagine there's a virtual link
    between each pairs of nodes, identified by three quadratic parameters (a, b, c)

When assigning the first task, choose the node that will result in minimum execution time
When assigning later tasks, iterate over each node, calculate the finish time on this node,
    and the finish time of parent node to child node link, choose a node such that max of ALL resource takeup time is 
    minimized
"""

__author__ = "Ouyang Liduo, Quynh Nguyen, Aleksandra Knezevic, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import create_input
from create_input import init
from copy import deepcopy
import numpy as np
import os
import time
import split
import random

class Duration:
    """Time duration about a task
    
    Attributes:
        -   end (float): ending time
        -   start (float): starting time
        -   task_num (int): task ID number
    """
    
    def __init__(self, task, start, end):
        self.task_num = task
        self.start = start
        self.end = end

class LinkDuration:
    """Time duration about an inter-task transfer on a (virtual) link
    this doesn't represent the virtual link itself, which is a node-to-node class
    this is a task-to-task class
    
    Attributes:
        -   end (float): ending time
        -   start (float): starting time
        -   start_task_num (int): task ID number of transfer source
        -   end_task_num (int): task ID number of transfer destination
    """
    
    def __init__(self, task1, task2, start, end):
        self.start_task_num = task1
        self.end_task_num = task2
        self.start = start
        self.end = end

class Task:
    """Task class represent a task
    """
    
    def __init__(self, num):
        self.number = num
        self.processor_num = -1
        self.up_rank = -1
        self.comp_cost = []
        self.avg_comp = 0
        self.parents_numbers = []
        # a map from all the processors where this task is assigned (split), to the task's portion on the processor
        # if no split (only original processor), this field is left empty
        self.proc_num_to_portion = {}

class Processor:
    """Processor class represent a processor
    """
    
    def __init__(self, num):
        self.number = num
        self.time_line = []

class Link:
    """Link class represent a VIRTUAL link
    Represent a node (processor) by node number, represent a link by id: string '{node1}_{node2}'
    """

    def __init__(self, node1, node2):
        self.id = str(node1) + '_' + str(node2)
        self.time_line = []
 
class HEFT:
    """A class of scheduling algorithm
    """

    def __init__(self, filename):
        """
        Initialize some parameters.
        """
        NODE_NAMES = os.environ["NODE_NAMES"]
        self.node_info = NODE_NAMES.split(":")
        self.num_task, self.task_names, self.num_processor, self.comp_cost, self.rate, self.data,self.quaratic_profile = init(filename)
        '''
        example output in a 3-node DAG:
        self.num_task: 4 
        self.task_names: ['task0', 'task1', 'task2', 'task3']
        self.num_processor: 2
        self.comp_cost: [[50, 50], [20, 20], [10, 10], [30, 30]]
        self.rate: [[0, 1], [1, 0]]
        self.data: [[-1, 67108, 67108, -1], [-1, -1, -1, 67108], [-1, -1, -1, 67108], [-1, -1, -1, -1]]
        self.quaratic_profile: [[(0, 0, 0), (0.0002541701921502464, -2.2216230193642272, 1777.3867073476163)], [(-4.191647173339474e-07, 0.050132222312572056, 236.0932576449177), (0, 0, 0)]]
        '''
        self.tasks = [Task(n) for n in range(self.num_task)]
        self.processors = [Processor(n) for n in range(self.num_processor)]
        self.get_parents_for_all()
        self.start_task_num, self.end_task_num = 0, self.num_task-1
        self.dup_tasks = []
        self.critical_pre_task_num = -1
        self.links = []

        # create empty virtual links
        for i in range(self.num_processor):
            for j in range(self.num_processor):
                if i == j: continue
                self.links.append(Link(i, j))
        
        for i in range(self.num_task):
            self.tasks[i].comp_cost = self.comp_cost[i]

        for task in self.tasks:
            task.avg_comp = sum(task.comp_cost) / self.num_processor
        
        self.cal_up_rank(self.tasks[self.start_task_num])
        # self.cal_down_rank(self.tasks[self.end_task_num])
        self.tasks.sort(cmp=lambda x, y: cmp(x.up_rank, y.up_rank), reverse=True)
        

    def cal_up_rank(self, task):
        """
        Calculate the upper rank of all tasks.
        
        Args:
            task (str): the entry node of the DAG
        """
        longest = 0
        for successor in self.tasks:
            if self.data[task.number][successor.number] != -1:
                if successor.up_rank == -1:
                    self.cal_up_rank(successor)

                longest = max(longest, self.cal_avg_comm(task, successor) + successor.up_rank)

        task.up_rank = task.avg_comp + longest

    def cal_down_rank(self, task):
        """
        Calculate the down rank of all tasks.

        Args:
            task (str): the exit node of the DAG.
        """
        if task == self.tasks[self.start_task_num]:
            task.down_rank = 0
            return
        for pre in self.tasks:
            if self.data[pre.number][task.number] != -1:
                if pre.down_rank == -1:
                    self.cal_down_rank(pre)

                task.down_rank = max(task.down_rank,
                                     pre.down_rank + pre.avg_comp + self.cal_avg_comm(pre, task))

    # Modified communication part
    def cal_est(self, task, processor):
        """
        Calculate the earliest start time of task on processor.
        
        Args:
            - task (str): the task name
            - processor (str): the processor name
        
        Returns:
            TYPE: estimated execution time of the task on the processor
        """
        est = 0
        for pre in self.tasks:
            if self.data[pre.number][task.number] != -1:
                if pre.processor_num != processor.number:
                    for dup_task in self.dup_tasks:
                        if dup_task.number == pre.number and dup_task.processor_num == task.processor_num:
                            c = 0
                            break
                    else:
                        c = self.cal_comm_quadratic(self.data[pre.number][task.number],self.quaratic_profile[pre.processor_num][processor.number])
                else:
                    c = 0
                if pre.aft + c > est:
                    est = pre.aft + c
                    self.critical_pre_task_num = pre.number

                #est = max(est, pre.aft + c)

        time_slots = []
        if len(processor.time_line) == 0:
            time_slots.append([0, 9999999999])
        else:
            for i in range(len(processor.time_line)):
                if i == 0:
                    if processor.time_line[i].start != 0:
                        time_slots.append([0, processor.time_line[i].start])
                    else:
                        continue
                else:
                    time_slots.append([processor.time_line[i - 1].end, processor.time_line[i].start])
            time_slots.append([processor.time_line[len(processor.time_line) - 1].end, 9999999999])


        for slot in time_slots:
            if est < slot[0] and slot[0] + task.comp_cost[processor.number] <= slot[1]:
                return slot[0]
            if est >= slot[0] and est + task.comp_cost[processor.number] <= slot[1]:
                return est
        # TODO: Possible bug here. If the value of est is larger than 9999 it returns an empty array which creates failts.
        # So added a default return statement to always return something. Not sure whether it is correct
        return est
        
    def cal_comm_quadratic(self,file_size,quaratic_profile):
        """communication quadratic information
        
        Args:
            - file_size (int): size of transfer files
            - quaratic_profile (list): includes quadratic information of the link
        
        Returns:
            float: predicted transfer time
        """
        return (np.square(file_size)*quaratic_profile[0] + file_size*quaratic_profile[1] + quaratic_profile[2])


    def cal_avg_comm(self, task1, task2):
        """
        Calculate the average communication cost between task1 and task2.
        
        Args:
            - task1 (str): the parent task
            - task2 (str): the child task
        
        Returns:
            float: predicted transfer time between the parent task and its child
        """

        #self.data[task1.number][task2.number] Kbit
        res = 0
        for i in range(self.num_processor):
            for j in range(self.num_processor):
                if i==j: continue
                res += self.cal_comm_quadratic(self.data[task1.number][task2.number],self.quaratic_profile[i][j])
        if(res < 0):
            print("got negative communication cost from network profiler, something wrong with DRUPE")
            print(self.task_names[task1.number], self.task_names[task2.number])
            for i in range(self.num_processor):
                for j in range(self.num_processor):
                    if i==j: continue
                    print(i, j)
                    print(self.cal_comm_quadratic(self.data[task1.number][task2.number],self.quaratic_profile[i][j]))
            exit()
        return res / (self.num_processor ** 2 - self.num_processor)


    def duplicate(self):
        """
        Reduce the communication overhead according copying the redundant tasks.
        """
        for pre_task in self.tasks:
            pre_processor_num = pre_task.processor_num
            for task in self.tasks:
                if pre_task == task or task.pre_task_num != pre_task.number:
                    continue
                processor_num = task.processor_num
                if pre_processor_num == processor_num:
                    continue
                dup_task_ast = self.cal_est(pre_task, self.processors[processor_num])
                dup_task_aft = dup_task_ast + pre_task.comp_cost[processor_num]
                if dup_task_aft > task.ast:
                    continue

                dup_task = Task(pre_task.number)
                dup_task.ast = dup_task_ast
                dup_task.aft = dup_task_aft
                dup_task.processor_num = processor_num
                self.dup_tasks.append(dup_task)
                self.processors[dup_task.processor_num].time_line.append(
                                Duration(-1, dup_task.ast, dup_task.aft))
                self.processors[processor_num].time_line.sort(cmp=lambda x, y: cmp(x.start, y.start))
                print('task %d dup on %s' % (pre_task.number, self.node_info[processor_num]))

    def reschedule(self):
        """
        After duplication, you should reschedule all tasks except redundant tasks.
        """
        # clear the time line list
        for p in self.processors:
            p.time_line = filter(lambda duration: duration.task_num == -1, p.time_line)

        for task in self.tasks:
            processor_num = task.processor_num
            est = self.cal_est(task, self.processors[processor_num])
            task.ast = est
            task.aft = est + task.comp_cost[processor_num]
            self.processors[task.processor_num].time_line.append(Duration(task.number, task.ast, task.aft))
            self.processors[processor_num].time_line.sort(cmp=lambda x, y: cmp(x.start, y.start))


    def run(self):
        
        for task in self.tasks:
            if task == self.tasks[0]:
                w = min(task.comp_cost)
                p = task.comp_cost.index(w)
                task.processor_num = p
                task.ast = 0
                task.aft = w
                self.processors[p].time_line.append(Duration(task.number, 0, w))
            else:
                aft = 9999999999
                for processor in self.processors:
                    est = self.cal_est(task, processor)
                    # print("est:", est)
                    # print("task:",task.comp_cost[processor.number])
                    print(processor.number, task.number)
                    if est + task.comp_cost[processor.number] < aft:
                        aft = est + task.comp_cost[processor.number]
                        p = processor.number
                        # Find the critical pre task
                        task.pre_task_num = self.critical_pre_task_num

                task.processor_num = p
                task.ast = aft - task.comp_cost[p]
                task.aft = aft
                self.processors[p].time_line.append(Duration(task.number, task.ast, task.aft))
                self.processors[p].time_line.sort(cmp=lambda x, y: cmp(x.start, y.start))

        #self.duplicate()
        #self.reschedule()

    
    
    def run_dup_split(self):
        while True:
            btnk_id = self.get_btnk_id()
            spt = split.Split()
            if self.is_link(btnk_id):
                src_node = btnk_id.split('_')[0]
                dst_node = btnk_id.split('_')[1]
                flag = True
                if self.get_node_by_id(int(src_node)).time_line[-1].end > self.get_node_by_id(int(dst_node)).time_line[-1].end:
                    flag = spt.do_split(self.links, self.processors, self.tasks, self.comp_cost, self.data, self.quaratic_profile, src_node)
                else:
                    flag = spt.do_split(self.links, self.processors, self.tasks, self.comp_cost, self.data, self.quaratic_profile, dst_node)
                if flag == False:
                    break
            else:
                flag = spt.do_split(self.links, self.processors, self.tasks, self.comp_cost, self.data, self.quaratic_profile, btnk_id)
                if flag == False:
                    break
            
    def get_node_by_id(self, num):
        for proc in self.processors:
            if proc.number == num:
                return proc
            
    def get_link_by_id(self, link_id):
        for l in self.links:
            if l.id == link_id:
                return l
             
    def get_parents_for_all(self):
        for task in self.tasks:
            for parent in self.tasks:
                if self.data[parent.number][task.number] != -1:
                    task.parents_numbers.append(parent.number)
                    
    def get_task_by_number(self, task_num):
        for tk in self.tasks:
            if tk.number == task_num:
                return tk
                    
    def display_result(self, level):
        """Display scheduling result to console
        """
        self.print_level(level)
        print("==============================================")
        print("               print task info")
        print("==============================================")
        print("task_number            task_uprank")
        for task in self.tasks:
            print(task.number, "              ", task.up_rank)
        
        print("==============================================")
        print("               print processor info")
        print("==============================================")
        print("processor_number     task_number     start_time     end_time")
        for processor in self.processors:
            for tl in processor.time_line:
                print("     ", processor.number, "      ", tl.task_num, "    ", tl.start, "    ", tl.end)
                
       
        print("==============================================")
        print("               print link info")
        print("==============================================")
        print("link_name    start_task_num   end_task_num   start_time   end_time") 
        for link in self.links:
            for tl in link.time_line:
                print(link.id, "      ", tl.start_task_num, "      ", tl.end_task_num, "       ", tl.start, "      ", tl.end)
        

    # output file is input_to_CIRCE
    def output_file(self, file_path):
        """Output scheduling to file
        
        Args:
            file_path (str): path of output file
        """
        output = open(file_path,"a")
        num = len(self.data)
        
        for task in self.tasks:
            if len(task.proc_num_to_portion) == 0:
                output.write(self.task_names[task.number] + " " + self.node_info[task.processor_num+1] + "\n")
            else:
                task_name = self.task_names[task.number]
                output.write(task_name + "   ")
                for proc_num in task.proc_num_to_portion:
                    output.write(self.node_info[proc_num+1] + "," + str(task.proc_num_to_portion[proc_num]) + " ")
                output.write('\n')
        output.close()

    def output_assignments(self):
        """Output the scheduling and corresponding assignments to ``assignments`` dictionary
        
        Returns:
            dict: assignments of tasks and corresponding computing nodes & portion
        """
        # eg a['task0'] = ['node1', 0.5, 'node2', 0.5], a['task1'] = 'node1'
        # if task wasn't split, value is a string specifying the node
        # else, value is a list, [node, portion, node, portion, etc]
        assignments = {}
        
        for task in self.tasks:
            if len(task.proc_num_to_portion) == 0:
                assignments[self.task_names[task.number]] = self.node_info[task.processor_num+1]
            else:
                task_name = self.task_names[task.number]
                assignments[task_name] = []
                for proc_num in task.proc_num_to_portion:
                    assignments[task_name].append(self.node_info[proc_num+1])
                    assignments[task_name].append(task.proc_num_to_portion[proc_num])
                    
        return assignments

    def print_level(self, level):
        """
        print put info according to level
        level = 0: tpheft
        level = 1: tpheft + dup
        level = 2: tpheft + split
        level = 3: tpheft + dup + split
        """
        if level == 0:
            print("#############################################################################################")
            print("                                   result for tpheft")
            print("#############################################################################################")
        elif level == 1:
            print("#############################################################################################")
            print("                                 result for tpheft + dup")
            print("#############################################################################################")
        elif level == 2:
            print("#############################################################################################")
            print("                                result for tpheft + split")
            print("#############################################################################################")
        elif level == 3:
            print("#############################################################################################")
            print("                             result for tpheft + dup + split")
            print("#############################################################################################")
        else:
            print("#############################################################################################")
            print("                               INVALID PRINT LEVEL NUMBER!!!")
            print("#############################################################################################")

    def get_btnk_id(self):
        """
        given current processor and link usage, return the id of resource with max takeup time 
        (without considering pipelined wait times)
        input: an array of links and an array of processors (with takeup time)
        output: id of bottleneck resource (string)
        """
        max_time = 0
        btnk_id = ""
        for link in self.links:
            if len(link.time_line) != 0:
                if link.time_line[-1].end > max_time:
                    max_time = link.time_line[-1].end
                    btnk_id = link.id
                    
        for processor in self.processors:
            if len(processor.time_line) != 0:
                if processor.time_line[-1].end > max_time:
                    max_time = processor.time_line[-1].end
                    btnk_id = str(processor.number)
                    
        return btnk_id
        
    def is_link(self, btnk_id):
        """
        return true if the bottleneck id represents a link
        false if processor
        """
        for c in btnk_id:
            if c == '_':
                return True
        return False
