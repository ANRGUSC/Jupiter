from flask import Flask, jsonify, request, render_template
from os import path
import os
from flask_cors import CORS
import json
import time

import subprocess
import sys
sys.path.append(path.abspath(__file__ + "/../../../../"))
import jupiter_config

# from demo import get_plot1, get_plot2, get_plot3, get_plot4
import demo
from bokeh.embed import server_document
from bokeh.server.server import Server
from tornado.ioloop import IOLoop
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler


cors = CORS()


# instantiate the app
app = Flask(__name__)
cors.init_app(app)


# set config
app_settings = os.getenv('APP_SETTINGS')
app.config.from_object(app_settings)


@app.route('/data', methods=['POST'])
def add_data():
    post_data = request.get_json()

    app_path = post_data.get('appPath')
    root_path = path.abspath('../../')
    config_file_path = '%s/jupiter_config.py' % (root_path)
    modify_app_path_file(config_file_path, app_path)

    nodes_info = post_data.get('nodes')
    node_file_path = '%s/nodes.txt' % (root_path)
    modify_nodes_file(node_file_path, nodes_info)

    task_mapper_option = post_data.get('SCHEDULER')
    ini_file_path = '%s/jupiter_config.ini' % (root_path)
    modify_task_mapper_option(ini_file_path, task_mapper_option)

    response_object = {
        'status': 'success',
    }
    return jsonify(response_object), 201


def modify_app_path_file(file_path, app_path):
    with open(file_path, 'r+') as f:
        lines = f.readlines()
        count = 0
        for index, line in enumerate(lines):
            if(line.startswith('APP_NAME_INPUT') and count == 0):
                lines[index] = 'APP_NAME_INPUT = \'%s\'' % (app_path) + '\n'
                count += 1
    with open(file_path, 'w+') as f:
        for line in lines:
            f.write(line)
        f.close()


def modify_nodes_file(file_path, nodes_info):
    # node_num = nodes_info.get('nodesNum')
    node_details = nodes_info.get('nodesDetails')
    with open(file_path, 'w+') as f:
        f.write(node_details)
    with open(file_path, 'r+') as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            lines[index] = line.replace("\n", "") + ' root PASSWORD' + '\n'
    with open(file_path, 'w+') as f:
        for line in lines:
            f.write(line)
        f.close()


def modify_task_mapper_option(file_path, task_mapper_option):
    with open(file_path, 'r+') as f:
        lines = f.readlines()
        count = 0
        for index, line in enumerate(lines):
            if (line.startswith('    SCHEDULER') and count == 0):
                lines[index] = '    SCHEDULER = %s' % task_mapper_option + '\n'
                count += 1
    with open(file_path, 'w+') as f:
        for line in lines:
            f.write(line)
        f.close()


@app.route('/execution_profile', methods=['POST'])
def get_exec_profile_info():

    response_object = {"exec_profiler_info": {}}
    nodes = read_node_list(path.abspath(__file__ + '../../../../../') + "/nodes.txt")
    # nodes = ['home']
    print(nodes)
    get_k8s_exec_info()

    res = []
    try:
        for i, node in enumerate(nodes):
            exist = os.path.isfile('profiler_%s.txt'%(node))
            if not exist:
                run_command_get_file(node)
            f = open('profiler_%s.txt'%(node))
            print("The profiler %s txt file exists."%(node))
            lines = f.readlines()
            lines[0] = node
            json_string = json.dumps(lines)
            res.append(json_string)
            # print(res)
            file_exist = True
    except FileNotFoundError:
        response_object["exec_profiler_info"] = "The execute information for is not ready."
    response_object["exec_profiler_info"] = json.dumps(res)
    # print(response_object)
    return jsonify(response_object), 201

def get_k8s_exec_info():
    jupiter_config.set_globals()

    global exec_namespace, app_name, exec_home_pod_name
    exec_namespace = jupiter_config.EXEC_NAMESPACE
    app_name = jupiter_config.app_option

    cmd = "kubectl get pod -l app=%s-home --namespace=%s -o name" % (app_name, exec_namespace)
    cmd_output = get_command_output(cmd)

    exec_home_pod_name = cmd_output.split('/')[1].split('\\')[0]

def run_command_get_file(node):
    log_file = 'profiler_%s.txt' % (node)
    file_path = '%s/%s:/centralized_scheduler/profiler_files_processed/profiler_%s.txt' % (exec_namespace, exec_home_pod_name, node)
    cmd = "kubectl cp " + file_path + " "+ log_file

    print("RUN: " + cmd)
    os.system(cmd)


def get_command_output(command):
    command = command.split(" ")
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    # retcode = p.wait()
    output = str(output)
    return output


def read_node_list(path2):
    nodes = []
    node_file = open(path2, "r")
    for line in node_file:
        node_line = line.strip().split(" ")
        nodes.append(node_line[0])
    return nodes

# def get_plot():
# #     post_data = request.get_json()
# #     p = None
# #     if (post_data == 'node_info'):
#     p = get_plot2()

#     # following above points:
#     #  + pass plot object 'p' into json_item
#     #  + wrap the result in json.dumps and return to frontend
#     return json.dumps(json_item(p, "myplot"))



@app.route('/plot')
def demo_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    apps = {'/demo': Application(FunctionHandler(modify_doc))}
    server = Server(apps, io_loop=IOLoop(), port=5006)
    print("Start the bokeh server:")
    server.start()
    server.io_loop.start()
    return

def modify_doc(doc):
    demo.main(doc)


@app.route('/network_profile')
def get_network_statistics():

    response_object = {"network_profiler_info": {}}
    nodes = ["home"]

    # currenly only test working for heft task mapper
    get_k8s_mapper_info()

    try:
        exist = os.path.isfile('network_log.txt')
        if not exist:
            run_command_get_file_net()
        f = open('network_log.txt')
        print("The network_log txt file exists.")
        lines = f.readlines()
        json_string = json.dumps(lines)
        print(json_string)
    except FileNotFoundError:
        response_object["network_profiler_info"] = "The network information for is not ready."
    response_object["network_profiler_info"] = json_string
    return jsonify(response_object), 201

def get_k8s_mapper_info():
    jupiter_config.set_globals()

    global mapper_namespace, app_name, mapper_home_pod_name
    mapper_namespace = jupiter_config.MAPPER_NAMESPACE
    app_name = jupiter_config.app_option

    cmd = "kubectl get pod -l app=%s1-home --namespace=%s -o name" % (app_name, mapper_namespace)
    cmd_output = get_command_output(cmd)
    print(cmd)
    print(cmd_output)
    mapper_home_pod_name = cmd_output.split('/')[1].split('\\')[0]

def run_command_get_file_net():
    log_file = 'network_log.txt'
    file_path = '%s/%s:/heft/network_log.txt' % (mapper_namespace, mapper_home_pod_name)
    cmd = "kubectl cp " + file_path + " "+ log_file
    print("RUN: " + cmd)
    os.system(cmd)


def get_command_output(command):
    command = command.split(" ")
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    output = str(output)
    return output

