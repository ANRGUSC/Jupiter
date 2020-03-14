#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2020, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

from pprint import pprint
from dockerfile_parse import DockerfileParser

############################################ HOME DOCKER TEMPLATE #########################################################

template_home ="""\
# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04

RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -y openssh-server mongodb
ADD simulation/data_sources/requirements_data.txt /requirements.txt
RUN apt-get -y install build-essential libssl-dev libffi-dev python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y sshpass nano


RUN pip3 install -r requirements.txt
RUN echo '{username}:{password}' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN mkdir generated_stream 
# Add the task speficific configuration files
ADD {app_file}/configuration.txt /configuration.txt
ADD simulation/data_sources/ds_test.py /ds_test.py
ADD simulation/data_sources/generate_random_files /generate_random_files
RUN chmod +x /generate_random_files

ADD nodes.txt /nodes.txt
ADD jupiter_config.ini /jupiter_config.ini

ADD simulation/data_sources/start_home.sh /start.sh
RUN chmod +x /start.sh

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]
"""



############################################ WORKER DOCKER TEMPLATE#########################################################


def write_stream_home_docker(app_option=None,**kwargs):
    """
        Function to Generate the Dockerfile of the home/master node of CIRCE
    """
    if app_option==None:
      file_name = 'home_node.Dockerfile'
    else:
      file_name = 'home_node_%s.Dockerfile'%(app_option)
    dfp = DockerfileParser(path=file_name)
    dfp.content =template_home.format(**kwargs)
    return file_name


if __name__ == '__main__':
    write_stream_home_docker(username = 'root',
                      password = 'PASSWORD',
                      app_file='app_specific_files/network_monitoring',
                      ports = '22 8888')