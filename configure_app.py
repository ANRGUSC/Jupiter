"""Configure Jupiter for an application.
This script reads an app_config.yaml file and generates all the Jupiter
configuration files needed. All Jupiter configuration files generated are
required and the structure should not be changed as the files will be
deprecated in the future.
Usage:
    Configure app at directory specified in jupiter_config.py. Example:
        $ python configure_app.py
    Configure app at manual relative directory. Example:
        $ python configure_app.py app_specific_files/example/
    Clean app files at directory specified in jupiter_config.py. Example:
        $ python configure_app.py clean
    Clean app files at manual relative directory. Example:
        $ python configure_app.py app_specific_files/example/ clean
"""

import jupiter_config
import yaml
import logging
import os
import sys
import json

# TODO: load logging level from top-level jupiter_config.ini
# change to INFO when done
logging.basicConfig(level=logging.DEBUG)


def get_app_path_from_jupiter():
    jupiter_config.set_globals()
    app_path = jupiter_config.APP_NAME
    return app_path


def load_yaml(filename):
    """
    Parse yaml file into python dictionary
    :type       filename:  path to file
    :param      filename:  string
    :returns:   python dictionary of yaml contents
    :rtype:     dict
    """
    with open(filename) as f:
        app_config = yaml.load(f, Loader=yaml.FullLoader)
        logging.debug(app_config)
    return app_config


def identify_dag_tasks(app_config, app_path):
    """
    Determine tasks that are part of the DAG. Non-DAG tasks are not run in the
    execution profiler.
    Generates file "{app_path}/scripts/config.json"
    :type       app_config:  python dict of parsed app_config.yaml
    :param      app_config:  dict
    :type       app_path:    path to Jupiter application files
    :param      app_path:    string
    """
    filename = app_path + "/scripts/config.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    dag_indicator = {
        "taskname_map": {

        },
        "exec_profiler": {

        }
    }

    for task in app_config['application']['task_list']['worker_tasks']:
        taskname = task['name']
        if task['dag_task'] is True:
            dag_indicator['taskname_map'][taskname] = [taskname, True]
            dag_indicator['exec_profiler'][taskname] = True
        elif task['dag_task'] is False:
            dag_indicator['taskname_map'][taskname] = [taskname, False]
            dag_indicator['exec_profiler'][taskname] = False
        else:
            logging.error("dag_task key-value incorrect")
            exit()

    # TODO: parse sources and sinks and set them as non DAG tasks

    with open(filename, "w") as f:
        f.write(json.dumps(dag_indicator, indent=4))

    logging.info("created " + filename)


def parse_node_list(app_config, app_path):
    """
    Identify nodes in Kubernetes cluster. This fucntion maps a Jupiter node
    name to the nodes hostname from `kubectl get nodes`.
    Generates file "{JUPITER_ROOT}/nodes.txt"
    :param      app_config:  python dict of app_config.yaml file
    :type       app_config:  dict
    :param      app_path:    path to Jupiter application files
    :type       app_path:    string
    """
    with open('nodes.txt', "w") as f:
        for node in app_config['node_list']:
            f.write(node + ' ' + app_config['node_list'][node])
            f.write('\n')

    logging.info("created " + 'nodes.txt')


def parse_dag_configuration(app_config, app_path):
    """
    Configure DAG structure and input/output behaviors.
    Generates file "{app_path}/configuration.txt"
    :param      app_config:  python dict of app_config.yaml file
    :type       app_config:  dict
    :param      app_path:    path to Jupiter application files
    :type       app_path:    string
    """

    # Populate tasklist to check DAG correctness
    tasklist = ['home']  # 'home' always exists
    for task in app_config['application']['task_list']['worker_tasks']:
        tasklist.append(task['name'])

    filename = app_path + "/configuration.txt"
    with open(filename, "w") as f:
        f.write(str(app_config['application']['num_tasks']))
        f.write('\n')
        for task in app_config['application']['task_list']['worker_tasks']:
            f.write(task['name'])
            f.write(' ' + str(task['inputs_to_wait_for']))

            if task['output_policy'] == 'BATCHED_ROUND_ROBIN':
                f.write(' ' + 'false')
            elif task['output_policy'] == 'POINT_TO_POINT_BROADCAST':
                f.write(' ' + 'true')
            elif task['output_policy'] == 'BATCHED_CUSTOM_ORDER':
                f.write(' ' + 'ordered')
            elif task['output_policy'] == 'UNICAST':
                f.write(' ' + 'exclusive')
            elif task['output_policy'] == 'NONE':
                f.write(' ' + 'none')

            try:
                if task['children'] is not None:
                    for child in task['children']:
                        if child not in tasklist:
                            logging.error("At least one child task does not " +
                                          "exist in task_list. Aborting!")
                            exit()
                        f.write(' ' + child)
            except KeyError:
                logging.debug("no children for task {}".format(task['name']))

            f.write('\n')

    logging.info("created " + filename)


def config_io_prefixes(app_config, app_path):
    """
    Parses the input and output file prefixes. These prefixes are needed to
    gather performance statistics of Jupiter. While a DAG application is
    running a background service will monitor files with these prefixes to
    measure metrics such as the time it takes to complete a job or transfer a
    job to another node.
    Generates file "{app_path}/name_convert.txt"
    :param      app_config:  python dict of app_config.yaml file
    :type       app_config:  dict
    :param      app_path:    path to Jupiter application files
    :type       app_path:    string
    """
    filename = app_path + '/name_convert.txt'
    with open(filename, "w") as f:
        for task in app_config['application']['task_list']['worker_tasks']:
            f.write(task['name'] + ' ' + task['outfile_prefix'] + ' ' +
                    task['infile_prefix'])
            f.write('\n')

    logging.info("created " + filename)


def config_docker_k8s_ports(app_config, app_path):
    """
    Parses the ports to expose at the Docker container and Kubernetes service
    levels. This is mainly used by the execution profiler, but it is also used
    by various subsystems.
    Generates file "{app_path}/app_config.ini"
    :param      app_config:  python dict of app_config.yaml file
    :type       app_config:  dict
    :param      app_path:    path to Jupiter application files
    :type       app_path:    string
    """
    filename = app_path + '/app_config.ini'
    with open(filename, "w") as f:
        f.write('[DOCKER_PORT]\n')
        for port in app_config['application']['ports']:
            f.write('    PYTHON-PORT = ' + str(port) + '\n')
        f.write('[SVC_PORT]\n')
        for port in app_config['application']['ports']:
            f.write('    PYTHON-PORT = ' + str(port) + '\n')

    logging.info("created " + filename)


def cleanup_files(app_path):
    try:
        logging.debug("deleting ./nodes.txt")
        os.remove('nodes.txt')
    except OSError:
        pass

    app_files = ['scripts/config.json', 'app_config.ini',
                 'configuration.txt', 'name_convert.txt']
    for file in app_files:
        try:
            logging.debug("deleting " + app_path + '/' + file)
            os.remove(app_path + '/' + file)
        except OSError:
            pass


if __name__ == '__main__':
    if len(sys.argv) > 3:
        logging.error("too many arguments")
        exit()
    elif len(sys.argv) == 3:
        # clean files
        if sys.argv[2] == "clean":
            app_path = sys.argv[1]
            cleanup_files(app_path)
            exit()
        else:
            logging.error("invalid command")
            exit()
    elif len(sys.argv) == 2:
        if sys.argv[1] is 'clean':
            # clean files using jupiter path
            app_path = get_app_path_from_jupiter()
            cleanup_files(app_path)
            exit()
        else:
            # optional manual path input
            app_path = sys.argv[1]
    else:
        app_path = get_app_path_from_jupiter()

    app_config = load_yaml(app_path + "/app_config.yaml")
    identify_dag_tasks(app_config, app_path)
    parse_node_list(app_config, app_path)
    parse_dag_configuration(app_config, app_path)
    config_io_prefixes(app_config, app_path)
    config_docker_k8s_ports(app_config, app_path)