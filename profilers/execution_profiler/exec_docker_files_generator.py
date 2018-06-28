#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

from pprint import pprint
from dockerfile_parse import DockerfileParser

############################################ WORKER DOCKER TEMPLATE #########################################################

template_worker ="""\
FROM ubuntu:16.04

RUN apt-get -yqq update

RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get -yqq update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -yqq openssh-client openssh-server bzip2 wget net-tools sshpass screen
RUN apt-get install -y vim
RUN apt-get install g++ make openmpi-bin libopenmpi-dev -y
RUN apt-get install sudo -y
RUN apt-get install iproute2 -y

RUN apt-get install -y openssh-server
RUN echo '{username}:{password}' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD profilers/execution_profiler/requirements.txt /requirements.txt

RUN pip3 install -r requirements.txt

RUN mkdir -p /home/darpa/apps/data


# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD {app_file}/scripts/ /centralized_scheduler/
COPY {app_file}/sample_input /centralized_scheduler/sample_input

ADD {app_file}/configuration.txt /centralized_scheduler/DAG.txt

ADD profilers/execution_profiler/profiler_worker.py /centralized_scheduler/profiler.py

ADD profilers/execution_profiler/start_worker.sh /centralized_scheduler/start.sh
ADD scripts/keep_alive.py /centralized_scheduler/keep_alive.py
ADD profilers/execution_profiler/get_files.py /centralized_scheduler/get_files.py
ADD jupiter_config.ini /centralized_scheduler/jupiter_config.ini


WORKDIR /centralized_scheduler/

EXPOSE {ports}

CMD ["./start.sh"]"""



############################################ HOME DOCKER TEMPLATE#########################################################

template_home ="""\
# ** Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
# **     contributor: Pradipta Ghosh, Quynh Nguyen, Bhaskar Krishnamachari
# **     Read license file in main directory for more details

# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04

# Install required libraries
RUN apt-get -yqq update

RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get -yqq update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -yqq openssh-client openssh-server mongodb bzip2 wget net-tools sshpass screen
RUN apt-get install -y vim
RUN apt-get install g++ make openmpi-bin libopenmpi-dev -y
RUN apt-get install sudo -y
RUN apt-get install iproute2 -y

RUN apt-get install -y openssh-server

# Install required python libraries
ADD profilers/execution_profiler/requirements.txt /requirements.txt

RUN pip3 install -r requirements.txt


# Authentication
RUN echo '{username}:{password}' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Prepare MongoDB
RUN mkdir -p /mongodb/data
RUN mkdir -p /mongodb/log

ADD profilers/execution_profiler/central_mongod /central_mongod


RUN mkdir -p /centralized_scheduler/profiler_files
RUN mkdir -p /centralized_scheduler/generated_files
RUN mkdir -p /centralized_scheduler/profiler_files_processed



# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD {app_file}/scripts/ /centralized_scheduler/
COPY {app_file}/sample_input /centralized_scheduler/sample_input
RUN mkdir -p /home/darpa/apps/data


ADD {app_file}/configuration.txt /centralized_scheduler/DAG.txt

ADD profilers/execution_profiler/start_home.sh /centralized_scheduler/start.sh
ADD scripts/keep_alive.py /centralized_scheduler/keep_alive.py
ADD profilers/execution_profiler/profiler_home.py /centralized_scheduler/profiler_home.py
ADD jupiter_config.ini /centralized_scheduler/jupiter_config.ini


WORKDIR /centralized_scheduler/
RUN ls
# Prepare scheduling files
RUN chmod +x /centralized_scheduler/start.sh


# tell the port number the container should expose
EXPOSE {ports}

CMD ["./start.sh"]
"""

############################################ DOCKER GENERATORS #########################################################



def write_exec_worker_docker(**kwargs):
    """
      Function to Generate the Dockerfile of the worker nodes of Execution Profiler.
    """
    dfp = DockerfileParser(path='exec_worker.Dockerfile')
    dfp.content =template_worker.format(**kwargs)
    # print(dfp.content)


def write_exec_home_docker(**kwargs):
    """
      Function to Generate the Dockerfile of the home/master node
    """
    dfp = DockerfileParser(path='exec_home.Dockerfile')
    dfp.content =template_home.format(**kwargs)

if __name__ == '__main__':
    write_exec_home_docker(username = 'root',
                      password = 'PASSWORD',
                      app_file = 'app_specific_files/network_monitoring',
                      ports = '22 27017 57021 8888')

    write_exec_worker_docker(username = 'root',
                      password = 'PASSWORD',
                      app_file = 'app_specific_files/network_monitoring',
                      ports = '22 27017 57021 8888')