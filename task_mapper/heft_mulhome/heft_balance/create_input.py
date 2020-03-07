#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
   This file created input tgff file for the HEFT algorithm.
"""
__author__ = "Quynh Nguyen, Aleksandra Knezevic, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

import re
import os



def init(filename):
    """
    This function read the tgff file and
    build computation matrix, communication matrix, rate matrix.
    TGFF is a useful tool to generate directed acyclic graph, tfgg file represent a task graph.
    
    Args:
        filename (str): name of output TGFF file
    
    Returns:
        - int: number of tasks
        - list: task names
        - int: number of processors
        - list: computing matrix
        - list: rate matrix
        - list: file size transfer matrix
        - list: communication matrix
    """

    NODE_NAMES = os.environ["NODE_NAMES"]
    node_info = NODE_NAMES.split(":")
    node_ids = {v:k for k,v in enumerate(node_info)}

    f = open(filename, 'r')
    f.readline()
    f.readline()
    f.readline()

    # Calculate the amount of tasks
    num_of_tasks = 0
    task_names=[]
    myline = f.readline()
    while myline.startswith('\tTASK'):
        num_of_tasks += 1
        name = myline.strip().split()[1]
        task_names.append(name)
        myline=f.readline()
    print("task_names:", task_names)

    # Build a communication matrix
    data = [[-1 for i in range(num_of_tasks)] for i in range(num_of_tasks)]
    line = f.readline()
    while line.startswith('\tARC'):
        line = re.sub(r'\bt\d_', '', line)
        A = [int(s) for s in line.split() if s.isdigit()]
        i, j, d = [int(s) for s in line.split() if s.isdigit()]
        data[i][j] = d
        line = f.readline()

    while not f.readline().startswith('@computation_cost'):
        pass

    # Calculate the amount of processors
    num_of_processors = len(f.readline().split()) - 3

    # Build a computation matrix
    comp_cost = []
    line = f.readline()
    while line.startswith('  '):
        comp_cost.append(map(int, line.split()[-num_of_processors:]))
        line = f.readline()
    # Build a rate matrix
    rate = [[1 for i in range(num_of_processors)] for i in range(num_of_processors)]
    for i in range(num_of_processors):
        rate[i][i] = 0

    # Build a network profile matrix
    quaratic_profile = [[(0,0,0) for i in range(num_of_processors)] for i in range(num_of_processors)]
    while not f.readline().startswith('@quadratic'):
        pass
    line = f.readline()
    line = f.readline()

    while line.startswith('  '):
        info = line.strip().split()
        i= node_ids[info[0]]
        j= node_ids[info[1]]
        a,b,c = [float(s) for s in info[2:]]
        quaratic_profile[i-1][j-1] = tuple([a,b,c])
        line = f.readline()

    return [num_of_tasks, task_names, num_of_processors, comp_cost, rate, data, quaratic_profile]
