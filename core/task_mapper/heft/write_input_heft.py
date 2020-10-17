"""
   This file generate the TGFF file required as an input of HEFT
"""
__author__ = "Quynh Nguyen, Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"
import os
import time
from create_input import init
import csv
import logging
# This exists in a build/ folder created by build_push_mapper.py
from build.jupiter_utils import app_config_parser

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

"""Paths specific to container (see Dockerfile)"""
TGFF_FILE = '/jupiter/input.tgff'
APP_DIR = "/jupiter/build/app_specific_files/"


def create_input_heft(
    tgff_file,
    num_nodes,
    network_info,
    execution_info,
    task_names,
    dag_task_map,
    name_to_id,
    worker_node_names
):
    """Generate the TGFF file

    Args:
        - tgff_file (str): file of output TGFF file
        - num_nodes (int): number of nodes
        - network_info (list): network profling information
        - execution_info (list): execution profiler information
        - task_names (list): names of tasks ordered as per app_config.yaml
        - dag_task_map (dict): mapping of tasks to list of children without "home"
        - name_to_id (dict): mapping of Jupiter node name to enumerated ID
    """
    target = open(tgff_file, 'w')
    target.write('@TASK_GRAPH 0 {')
    target.write("\n")
    target.write('\tAPERIODIC')
    target.write("\n\n")

    task_map = ['t0_%d' % (i) for i in range(0, len(task_names))]
    task_ID_dict = dict(zip(task_names, range(0, len(task_names))))
    task_dict = dict(zip(task_names, task_map))

    computation_matrix = []
    for i in range(0, len(task_names)):
        task_times = [0 for i in range(num_nodes)]
        computation_matrix.append(task_times)

    task_size = {}

    # Read format: Node ID, Task, Execution Time, Output size
    for row in execution_info:
        computation_matrix[task_ID_dict[row[1]]][name_to_id[row[0]] - 1] = int(float(row[2]) * 10)
        # 100000
        task_size[row[1]] = row[3]

    for i in range(0, len(task_names)):
        line = "\tTASK %s\tTYPE %d \n" % (task_names[i], i)
        target.write(line)
    target.write("\n")

    # Need check
    v = 0
    keys = dag_task_map.keys()
    for key in keys:
        for j in range(0, len(dag_task_map[key])):
            # file size in Kbit is communication const
            comm_cost = int(float(task_size[key]))
            line = "\tARC a0_%d \tFROM %s TO %s \tTYPE %d" % (v, task_dict[key], task_dict.get(dag_task_map[key][j]), comm_cost)
            v = v + 1
            target.write(line)
            target.write("\n")
    target.write("\n")
    target.write('}')

    # OK
    target.write('\n@computation_cost 0 {\n')

    line = '# type version %s\n' % (' '.join(worker_node_names[:]))
    target.write(line)

    for i in range(0, len(task_names)):
        line = '  %s    0\t%s\n' % (task_dict.get(task_names[i]), ' '.join(str(x) for x in computation_matrix[i]))
        target.write(line)
    target.write('}')
    target.write('\n\n\n\n')

    target.write('\n@quadratic 0 {\n')
    target.write('# Source Destination a b c\n')

    # OK
    for row in network_info:
        line = '  %s\t%s\t%s\n'%(row[0], row[2], row[4])
        target.write(line)
    target.write('}')
    target.close()

    # do not care about outputs
    _, _, _, _, _, _, _ = init(tgff_file, worker_node_names)
    return

if __name__ == '__main__':
    app_config = app_config_parser.AppConfig(APP_DIR)
    task_names = app_config.get_dag_task_names()
    num_nodes = app_config.get_num_worker_nodes()

    # HEFT should only schedule tasks on worker nodes (not the home node)?
    worker_node_names = os.environ["WORKER_NODE_NAMES"].split(":")
    name_to_id = {v: k for k, v in enumerate(worker_node_names)}

    worker_names = []
    for name, k8s_host in app_config.node_map().items():
        if name != "home":
            worker_names.append(name)

    dag_task_map = app_config.dag_task_map()

    log.info('Creating input HEFT file...')
    while True:
        if os.path.isfile('/jupiter/execution_log.txt') and os.path.isfile('/jupiter/network_log.txt'):
            with open('/jupiter/network_log.txt', 'r') as f:
                reader = csv.reader(f)
                network_info = list(reader)
            with open('/jupiter/execution_log.txt', 'r') as f:
                reader = csv.reader(f)
                execution_info = list(reader)
            # fix non-DAG tasks (temporary approach)
            new_execution = []
            for row in execution_info:
                if row[0] != 'home':
                    new_execution.append(row)
                else:
                    log.debug(row)

            create_input_heft(
                TGFF_FILE,
                num_nodes,
                network_info,
                new_execution,
                task_names,
                dag_task_map,
                name_to_id,
                worker_node_names
            )
            break
        else:
            logging.info('HEFT input not yet created, retrying in 10s...')
            time.sleep(10)
