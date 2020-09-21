#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Pradipta Ghosh and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
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
ADD circe/original/requirements.txt /requirements.txt
RUN apt-get -y install build-essential libssl-dev libffi-dev python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y sshpass nano

# Taken from quynh's network profiler
RUN pip install cryptography

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN echo '{username}:{password}' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Create the mongodb directories
RUN mkdir -p /mongodb/data
RUN mkdir -p /mongodb/log

# Create the input, output, and runtime profiler directories
RUN mkdir -p /input
RUN mkdir -p /output
#RUN mkdir -p /runtime


RUN apt-get install stress

# Add input files
COPY  {app_file}/sample_input /sample_input

# Add the mongodb scripts
ADD circe/original/runtime_profiler_mongodb /central_mongod
#ADD circe/original/rt_profiler_update_mongo.py /run_update.py

ADD circe/original/readconfig.py /readconfig.py
ADD circe/original/scheduler.py /scheduler.py
ADD jupiter_config.py /jupiter_config.py
ADD circe/original/evaluate.py /evaluate.py


# Add the task speficific configuration files
ADD {app_file}/configuration.txt /configuration.txt

ADD nodes.txt /nodes.txt
ADD jupiter_config.ini /jupiter_config.ini

ADD circe/original/start_home.sh /start.sh
RUN chmod +x /start.sh
RUN chmod +x /central_mongod

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]
"""



############################################ WORKER DOCKER TEMPLATE#########################################################

template_worker ="""\
# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04

RUN apt-get -yqq update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev 
RUN apt-get install -yqq openssh-client openssh-server bzip2 wget net-tools sshpass screen
RUN apt-get install -y vim
RUN apt-get install g++ make openmpi-bin libopenmpi-dev -y
RUN apt-get install sudo -y
RUN apt-get install iproute2 -y

## Install TASK specific needs. The hadoop is a requirement for the network profiler application
##RUN wget http://supergsego.com/apache/hadoop/common/hadoop-2.8.1/hadoop-2.8.1.tar.gz -P ~/
RUN wget https://archive.apache.org/dist/hadoop/core/hadoop-2.8.1/hadoop-2.8.1.tar.gz -P ~/
RUN tar -zxvf ~/hadoop-2.8.1.tar.gz -C ~/
RUN rm ~/hadoop-2.8.1.tar.gz
RUN sudo apt update
RUN apt-get install -y mosquitto-clients

ADD circe/original/requirements.txt /requirements.txt

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN echo '{username}:{password}' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN mkdir -p /centralized_scheduler/input
RUN mkdir -p /centralized_scheduler/output
#RUN mkdir -p /centralized_scheduler/runtime
ADD circe/original/monitor.py /centralized_scheduler/monitor.py
RUN mkdir -p /home/darpa/apps/data

#ADD circe/original/rt_profiler_data_update.py  /centralized_scheduler/rt_profiler_data_update.py

# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD {app_file}/scripts/ /centralized_scheduler/

ADD jupiter_config.ini /jupiter_config.ini


ADD circe/original/start_worker.sh /start.sh
RUN chmod +x /start.sh

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]

"""

############################################ DOCKER GENERATORS #########################################################


  
def write_circe_worker_docker(app_option=None,**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    if app_option==None:
      file_name = 'worker_node.Dockerfile'
    else:
      file_name = 'worker_node_%s.Dockerfile'%(app_option)
    dfp = DockerfileParser(path=file_name)
    dfp.content =template_worker.format(**kwargs)
    return file_name
    # print(dfp.content)


def write_circe_home_docker(app_option=None,**kwargs):
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
    write_circe_home_docker(username = 'root',
                      password = 'PASSWORD',
                      app_file='app_specific_files/network_monitoring',
                      ports = '22 8888')

    write_circe_worker_docker(username = 'root',
                      password = 'PASSWORD',
                      app_file='app_specific_files/network_monitoring',
                      ports = '22 57021')
