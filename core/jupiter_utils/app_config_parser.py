import yaml
import logging
import json
import os

logging.basicConfig(format="%(levelname)s:%(filename)s:%(message)s")
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AppConfig:
    """
    This class is for parsing a Jupiter application's app_config.yaml file.
    """

    def __init__(self, app_dir):
        """
        AppConfig constructor.

        :param      app_dir:   The application dir
        :type       app_dir:   str
        :param      app_name:  The application name (optional)
        :type       app_name:  str
        """
        config_path = os.path.join(app_dir, "app_config.yaml")

        # app name is the same as the folder name
        self.app_name = os.path.basename(os.path.dirname(config_path))

        self.abs_app_dir = os.path.abspath(app_dir)
        with open(config_path) as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
            log.debug(json.dumps(self.cfg, indent=4))

        # developers: manually set a non-empty string to override docker tags.
        # this is useful for creating unique docker tags when multiple people
        # are coding.
        self.tag_extension = ""

    def get_dag_tasks(self):
        """
        Returns entire list of task information
        """
        return self.cfg['application']['tasks']['dag_tasks']

    def get_dag_task_names(self):
        task_names = []
        for item in self.cfg['application']['tasks']['dag_tasks']:
            task_names.append(item['name'])
        return task_names

    def get_nondag_tasks(self):
        tasks = []
        try:
            tasks = self.cfg['application']['tasks']['nondag_tasks']
        except TypeError:
            log.info("no non-DAG tasks found")

        return tasks

    def get_num_nodes(self):
        return len(self.cfg['node_map'])

    def get_num_worker_nodes(self):
        worker_nodes = self.cfg['node_map']
        del worker_nodes['home']
        return len(worker_nodes)

    def get_exec_home_tag(self):
        docker_registry = self.cfg['jupiter_config']['docker_registry']
        tag = "{}/exec_profiler_home:{}{}".format(
            docker_registry,
            self.app_name,
            self.tag_extension
        )
        return tag

    def get_exec_worker_tag(self):
        docker_registry = self.cfg['jupiter_config']['docker_registry']
        tag = "{}/exec_profiler_worker:{}{}".format(
            docker_registry,
            self.app_name,
            self.tag_extension
        )
        return tag

    def get_drupe_home_tag(self):
        docker_registry = self.cfg['jupiter_config']['docker_registry']
        tag = "{}/drupe_profiler_home:{}{}".format(
            docker_registry,
            self.app_name,
            self.tag_extension
        )
        return tag

    def get_drupe_worker_tag(self):
        docker_registry = self.cfg['jupiter_config']['docker_registry']
        tag = "{}/drupe_profiler_worker:{}{}".format(
            docker_registry,
            self.app_name,
            self.tag_extension
        )
        return tag

    def get_circe_tag(self):
        docker_registry = self.cfg['jupiter_config']['docker_registry']
        tag = "{}/circe:{}{}".format(
            docker_registry,
            self.app_name,
            self.tag_extension
        )
        return tag

    def get_mapper_tag(self):
        docker_registry = self.cfg['jupiter_config']['docker_registry']
        tag = "{}/mapper_home:{}{}".format(
            docker_registry,
            self.app_name,
            self.tag_extension
        )
        return tag

    def namespace_prefix(self):
        return self.cfg['jupiter_config']['namespace_prefix']

    def node_map(self):
        return self.cfg['node_map']

    def home_host(self):
        return self.cfg['node_map']['home']

    def child_tasks(self, task_name):
        if task_name == "home":
            return self.cfg['application']['tasks']['home']['children']

        for task in self.cfg['application']['tasks']['dag_tasks']:
            if task['name'] == task_name:
                return task['children']

        for nondag_task in self.cfg['application']['tasks']['nondag_tasks']:
            if nondag_task['name'] == task_name:
                return nondag_task['children']

        raise ChildTasksNotFoundError("No child tasks found")

    def task_mapper(self):
        return self.cfg['jupiter_config']['task_mapper']

    def dag_task_map(self):
        """ Creates a task map of the entire DAG. Returns a dictionary of task
        names to children excluding the "home" task/node (task and node is used
        interchangeably only for home)
        """
        task_map = {}
        for task in self.get_dag_tasks():
            task_name = task['name']
            task_map[task_name] = self.child_tasks(task_name)
            try:
                task_map[task_name].remove("home")
            except ValueError:
                pass  # do nothing
        return task_map

    def base_script(self, task_name):
        if task_name == "home":
            return self.cfg['application']['tasks']['home']['base_script']

        for task in self.cfg['application']['tasks']['dag_tasks']:
            if task['name'] == task_name:
                return task['base_script']

        for task in self.cfg['application']['tasks']['nondag_tasks']:
            if task['name'] == task_name:
                return task['base_script']

        raise BaseScriptNotFoundError("No base_script for task")

    def port_mappings(self):
        return self.cfg['application']['port_mappings']


if __name__ == '__main__':
    # Test
    app_config = AppConfig("../../app_specific_files/example/")
    for node in app_config.node_map():
        print(node)

    print("DAG task map: \n" + json.dumps(app_config.dag_task_map(), indent=4))
