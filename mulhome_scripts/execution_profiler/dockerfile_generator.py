#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

# ---- WORKER DOCKERFILE TEMPLATE ---- #
template_worker ="""\
FROM ubuntu:18.04

RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get -yqq update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -yqq openssh-client openssh-server bzip2 wget net-tools sshpass
RUN apt-get install -y vim stress

RUN echo '{username}:{password}' | chpasswd

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN service ssh restart

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# install execution profiler requirements
ADD requirements.txt /jupiter/requirements.txt
RUN pip3 install -r /jupiter/requirements.txt

# add all jupiter application files and install any requirements
COPY build/app_specific_files/ /jupiter/app_specific_files/
RUN pip3 install -r /jupiter/app_specific_files/requirements.txt

ADD profiler_worker.py /jupiter/profiler.py

ADD start_worker.sh /jupiter/start.sh
ADD get_files.py /jupiter/get_files.py
ADD build/jupiter_config.ini /jupiter/jupiter_config.ini

RUN chmod +x /jupiter/start_worker.sh

WORKDIR /jupiter/

EXPOSE {ports}

CMD ["./jupiter/start_worker.sh"]"""


# ---- HOME DOCKERFILE TEMPLATE ---- #
template_home ="""\
# ** Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved.
# **     contributor: Pradipta Ghosh, Quynh Nguyen, Bhaskar Krishnamachari
# **     Read license file in main directory for more details

# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:18.04

# Install required libraries
RUN apt-get -yqq update

RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get -yqq update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -yqq openssh-client openssh-server mongodb wget net-tools sshpass
RUN apt-get install -y vim

# Install required python libraries
ADD requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt


# Authentication
RUN echo '{username}:{password}' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN service ssh restart

#RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Prepare MongoDB
# RUN mkdir -p /mongodb/data
RUN mkdir -p /data/db
RUN mkdir -p /mongodb/log
RUN sed -i -e 's/bind_ip = 127.0.0.1/bind_ip =  127\.0\.0\.1, 0\.0\.0\.0/g' /etc/mongodb.conf

ADD central_mongod /central_mongod
RUN chmod +x /central_mongod


RUN mkdir -p /centralized_scheduler/profiler_files
RUN mkdir -p /centralized_scheduler/generated_files
RUN mkdir -p /centralized_scheduler/profiler_files_processed



# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD build/{app_dir}/scripts/ /centralized_scheduler/
# COPY build/{app_dir}/sample_input /centralized_scheduler/sample_input


ADD build/{app_dir}/configuration.txt /centralized_scheduler/DAG.txt
ADD build/nodes.txt /centralized_scheduler/nodes.txt

ADD start_home.sh /centralized_scheduler/start_home.sh
ADD profiler_home.py /centralized_scheduler/profiler_home.py
ADD build/jupiter_config.ini /centralized_scheduler/jupiter_config.ini


WORKDIR /centralized_scheduler/
RUN ls
# Prepare scheduling files
RUN chmod +x /centralized_scheduler/start_home.sh


# tell the port number the container should expose
EXPOSE {ports}

CMD ["./start_home.sh"]
"""


def write_exec_worker_docker(**kwargs):
    """
      Generate the Dockerfile for worker nodes of Execution Profiler.
    """
    return template_worker.format(**kwargs)


def write_exec_home_docker(**kwargs):
    """
      Generate the Dockerfile of the home/master node
    """
    return template_home.format(**kwargs)


if __name__ == '__main__':
    testfile = write_exec_home_docker(
        username='root',
        password='PASSWORD',
        app_dir='app_specific_files/network_monitoring',
        ports='22 27017 57021 8888'
    )

    print(testfile)

    testfile = write_exec_worker_docker(
        username='root',
        password='PASSWORD',
        app_dir='app_specific_files/network_monitoring',
        ports='22 27017 57021 8888'
    )

    print(testfile)
