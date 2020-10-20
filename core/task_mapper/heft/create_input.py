"""
   This file created input tgff file for the HEFT algorithm.
"""
__author__ = "Quynh Nguyen, Aleksandra Knezevic, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import re
import logging

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def init(filename, worker_node_names):
    """
    This function reads the TGFF file and builds a computation matrix,
    communication matrix, and rate matrix.

    TGFF is a useful tool to generate directed acyclic graph. The TGFF file
    represents a task graph.

    Args:
        filename (str): name of output TGFF file
        worker_node_names (str): Jupiter node names, separated by ':'

    Returns:
        - int: number of tasks
        - list: task names
        - int: number of processors
        - list: computing matrix
        - list: rate matrix
        - list: file size transfer matrix
        - list: communication matrix
    """
    node_ids = {v: k for k, v in enumerate(worker_node_names)}

    f = open(filename, 'r')
    f.readline()
    f.readline()
    f.readline()

    # Calculate the amount of tasks
    num_of_tasks = 0
    task_names = []
    myline = f.readline()
    while myline.startswith('\tTASK'):
        num_of_tasks += 1
        log.debug(myline)
        name = myline.strip().split()[1]
        task_names.append(name)
        log.debug(f"task names: {task_names}")
        myline = f.readline()
    log.debug(f"task_names: {task_names}")
    log.debug(f"Number of tasks = {num_of_tasks}")

    # Build a communication matrix
    data = [[-1 for i in range(num_of_tasks)] for i in range(num_of_tasks)]
    line = f.readline()
    while line.startswith('\tARC'):
        line = re.sub(r'\bt\d_', '', line)
        i, j, d = [int(s) for s in line.split() if s.isdigit()]
        data[i][j] = d
        line = f.readline()

    while not f.readline().startswith('@computation_cost'):
        pass

    # Calculate the amount of processors
    num_of_processors = len(f.readline().split()) - 3
    log.debug(f"Number of processors = {num_of_processors}")

    # Build a computation matrix
    comp_cost = []
    line = f.readline()
    while line.startswith('  '):
        comp_cost.append([int(i) for i in line.split()[-num_of_processors:]])
        line = f.readline()
    
    # Build a rate matrix
    rate = [[1 for i in range(num_of_processors)] for i in range(num_of_processors)]
    for i in range(num_of_processors):
        rate[i][i] = 0

    # Build a network profile matrix
    quadratic_profile = [[(0, 0, 0) for i in range(num_of_processors)] for i in range(num_of_processors)]
    while not f.readline().startswith('@quadratic'):
        pass
    line = f.readline()
    line = f.readline()

    while line.startswith('  '):
        info = line.strip().split()
        i = node_ids[info[0]]
        j = node_ids[info[1]]
        a, b, c = [float(s) for s in info[2:]]
        quadratic_profile[i - 1][j - 1] = tuple([a, b, c])
        line = f.readline()

    log.debug('==================')
    # logging.debug(quadratic_profile)
    return [num_of_tasks, task_names, num_of_processors, comp_cost, rate, data, quadratic_profile]
