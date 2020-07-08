
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

def get_tasks(app_config_path):
    app_config = load_yaml(app_config_path)
    task_list = []

    for task in app_config['application']['task_list']['worker_tasks']:
        task_list.append(task['name'])

    return task_list

def get_datasources(app_config_path):
    app_config = load_yaml(app_config_path)
    datasource_list = []

    for ds in app_config['application']['sources']:
        datasource_list.append(ds['name'])

    return datasource_list

def get_num_nodes(app_config_path):
    app_config = load_yaml(app_config_path)
    return len(app_config['node_list'])
