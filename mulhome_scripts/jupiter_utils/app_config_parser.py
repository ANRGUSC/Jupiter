import yaml
import logging
import json
import sys
from os import path

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AppConfig:
    """
    This class is for parsing a Jupiter application's app_config.yaml file.
    """
    def __init__(self, app_dir, app_name):
        """
        AppConfig constructor.
        
        :param      app_dir:   The application dir
        :type       app_dir:   str
        :param      app_name:  The application name (optional)
        :type       app_name:  str
        """
        config_path = path.join(app_dir, "app_config.yaml")
        self.app_name = app_name # used for k8s service/deployment specs
        self.abs_app_dir = path.abspath(app_dir)
        with open(config_path) as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
            log.debug(json.dumps(self.cfg, indent=4))

    def get_dag_tasks(self):
        """
        Returns entire list of task information
        """
        return self.cfg['application']['task_list']['worker_tasks']

    def get_sources(self):
        sources = []
        for ds in self.cfg['application']['sources']:
            sources.append(ds)
        return sources

    def get_source_names(self):
        names = []
        for ds in self.cfg['application']['sources']:
            names.append(ds['name'])
        return names

    def get_num_nodes(self):
        return len(self.cfg['node_list'])

    def get_exec_home_tag(self):
        docker_registry = self.cfg['jupiter_config']['docker_registry']
        tag = "{}/exec_profiler_home:{}".format(docker_registry, self.app_name)
        return tag

    def get_exec_worker_tag(self):
        docker_registry = self.cfg['jupiter_config']['docker_registry']
        tag = "{}/exec_profiler_worker:{}".format(docker_registry, self.app_name)
        return tag

    def namespace_prefix(self):
        return self.cfg['jupiter_config']['namespace_prefix']

    def node_list(self):
        return self.cfg['node_list']

    def home_host(self):
        return self.cfg['node_list']['home']

    def child_tasks(self, task_name):
        for task in self.cfg['application']['task_list']['worker_tasks']:
            if task['name'] == task_name:
                return task['children']
        raise ChildTasksNotFoundError("No child tasks found")

if __name__ == '__main__':
    app_config = AppConfig("../../app_specific_files/example_incomplete/")
    for node in app_config.node_list():
        print(node)
