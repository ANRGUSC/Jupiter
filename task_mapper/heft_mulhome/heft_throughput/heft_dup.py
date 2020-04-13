
"""
This module is the HEFT algorithm modifed based on the `source`_ by Ouyang Liduo.

.. _source: https://github.com/oyld/heft 

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


class Task:
    """Task class represent a task
    """
    
    def __init__(self, num):
        self.number = num
        self.ast = -1
        self.aft = -1
        self.processor_num = -1
        self.up_rank = -1
        self.down_rank = -1
        self.comp_cost = []
        self.avg_comp = 0
        self.pre_task_num = -1
        self.weight = 0

class Processor:

    """Processor class represent a processor
    """
    
    def __init__(self, num):
        self.number = num
        self.time_line = []

class Link:
    """Link class represent a VIRTUAL link
    consider both link and nodes as computation resources
    here we use virtual links, meaning imagine we have an independent link
    between each pair of nodes, and we try to balance the calculation time
    among them and the computing nodes
    """
 
class HEFT:
    """A class of scheduling algorithm
    """

    def __init__(self, filename):
        """
        Initialize some parameters.
        """
        NODE_NAMES = os.environ["NODE_NAMES"]
        self.node_info = NODE_NAMES.split(":")
        self.num_task, self.task_names, self.num_processor, comp_cost, self.rate, self.data,self.quaratic_profile = init(filename)
        '''
        example output in a 3-node DAG:
        self.num_task: 4 
        self.task_names: ['task0', 'task1', 'task2', 'task3']
        self.num_processor: 2
        comp_cost: [[50, 50], [20, 20], [10, 10], [30, 30]]
        self.rate: [[0, 1], [1, 0]]
        self.data: [[-1, 67108, 67108, -1], [-1, -1, -1, 67108], [-1, -1, -1, 67108], [-1, -1, -1, -1]]
        self.quaratic_profile: [[(0, 0, 0), (0.0002541701921502464, -2.2216230193642272, 1777.3867073476163)], [(-4.191647173339474e-07, 0.050132222312572056, 236.0932576449177), (0, 0, 0)]]
        '''
        self.tasks = [Task(n) for n in range(self.num_task)]
        self.processors = [Processor(n) for n in range(self.num_processor)]
        self.start_task_num, self.end_task_num = 0, self.num_task-1
        self.dup_tasks = []
        self.critical_pre_task_num = -1


        for i in range(self.num_task):
            self.tasks[i].comp_cost = comp_cost[i]

        for task in self.tasks:
            task.avg_comp = sum(task.comp_cost) / self.num_processor
        
        """ throughput optimized HEFT: try to balance the execution time among all nodes """
        
        '''
        step1: rank tasks in decreasing order by their 'weight'
               weight of a task is defined as the average computation time, plus the max of (parent weight + ave communication time)
        '''
        for task in self.tasks:
            self.cal_weight(task)
        self.tasks.sort(cmp=lambda x, y: cmp(x.weight, y.weight), reverse=True)
        
        '''
        step2: for task in decreasing order of weight, assign each task to a processor to minimize the max occupation time of
               all resources, including links and processors
        '''
        for task in self.tasks:
            
        
        self.cal_up_rank(self.tasks[self.start_task_num])
        self.cal_down_rank(self.tasks[self.end_task_num])

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
                                     
    def cal_weight(self, task):
    """
    """
        if task.weight != 0:
            return 
        if task == self.tasks[self.start_task_num]:
            task.weight = task.ave_comp
            return
        max_parent_cost = 0
        for parent in self.tasks:
            if self.data[parent.number][task.number] != -1:
                if parent.weight == 0:
                    cal_weight(parent)
                max_parent_cost = max(max_parent_cost, parent.weight + cal_avg_comm(parent, task)) 
        task.weight = max_parent_cost + task.ave_comp
        
        
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
            exit()
        return res / (self.num_processor ** 2 - self.num_processor)


    def reschedule(self):
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
                aft = 9999
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

        self.duplicate()
        self.reschedule()




    def display_result(self):
        """Display scheduling result to console
        """
        for t in self.tasks:
            print('task %d : up_rank = %f, down_rank = %f' % (t.number, t.up_rank, t.down_rank))
            if t.number == self.end_task_num:
                makespan = t.aft

        for p in self.processors:
            print('%s:' % (self.node_info[p.number + 1]))
            for duration in p.time_line:
                if duration.task_num != -1:
                    print('task %d : ast = %d, aft = %d' % (duration.task_num + 1,
                                                            duration.start, duration.end))

        for dup in self.dup_tasks:
            print('redundant task %s on %s' % (dup.number + 1, self.node_info[dup.processor_num + 1]))

        print('makespan = %d' % makespan)

    def output_file(self,file_path):
        """Output scheduling to file
        
        Args:
            file_path (str): path of output file
        """
        output = open(file_path,"a")
        num = len(self.data)
        for p in self.processors:
            for duration in p.time_line:
                if duration.task_num != -1:
                    output.write(self.task_names[duration.task_num] + " " + self.node_info[p.number+1])
                    output.write('\n')

        output.close()

    def output_assignments(self):
        """Output the scheduling and corresponding assignments to ``assignments`` dictionary
        
        Returns:
            dict: assignments of tasks and corresponding computing nodes
        """
        assignments = {}
        for p in self.processors:
            for duration in p.time_line:
                if duration.task_num != -1:
                    assignments[self.task_names[duration.task_num]] = self.node_info[p.number+1]
        return assignments




