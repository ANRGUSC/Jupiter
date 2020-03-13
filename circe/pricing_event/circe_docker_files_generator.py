#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Pradipta Ghosh, Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

from pprint import pprint
from dockerfile_parse import DockerfileParser

############################################ HOME DOCKER TEMPLATE #########################################################

template_home ="""\
# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04

RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -y openssh-server mongodb
ADD circe/{pricing_option}/requirements.txt /requirements.txt
RUN apt-get -y install build-essential libssl-dev libffi-dev python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y sshpass nano

# Taken from quynh's network profiler
RUN pip install cryptography


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

# Create the input, output
RUN mkdir -p /input
RUN mkdir -p /output

# Add input files
COPY  {app_file}/sample_input /sample_input

# Add the mongodb scripts
ADD circe/{pricing_option}/runtime_profiler_mongodb /central_mongod

ADD circe/{pricing_option}/readconfig.py /readconfig.py
ADD circe/{pricing_option}/scheduler.py /scheduler.py
ADD jupiter_config.py /jupiter_config.py
ADD circe/{pricing_option}/evaluate.py /evaluate.py

# Add the task speficific configuration files
RUN echo {app_file}/configuration.txt
ADD {app_file}/configuration.txt /configuration.txt
ADD nodes.txt /nodes.txt
ADD jupiter_config.ini /jupiter_config.ini

ADD circe/{pricing_option}/monitor.py /centralized_scheduler/monitor.py
ADD circe/{pricing_option}/start_home.sh /start.sh
RUN chmod +x /start.sh
RUN chmod +x /central_mongod
ADD {app_file}/name_convert.txt /centralized_scheduler/name_convert.txt
ADD {app_file}/sample_input/1botnet.ipsum /centralized_scheduler/1botnet.ipsum

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]
"""



############################################ WORKER DOCKER TEMPLATE#########################################################

template_controller_worker ="""\
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
ADD circe/{pricing_option}/requirements.txt /requirements.txt

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
RUN mkdir -p /centralized_scheduler/sample_input
RUN mkdir -p /home/darpa/apps/data

# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD {app_file}/scripts/ /centralized_scheduler/
ADD {app_file}/sample_input/ /centralized_scheduler/sample_input/
ADD {app_file}/configuration.txt  /centralized_scheduler/dag.txt

ADD jupiter_config.ini /jupiter_config.ini
ADD jupiter_config.py /jupiter_config.py

#ADD circe/{pricing_option}/monitor.py /centralized_scheduler/monitor.py
ADD circe/{pricing_option}/start_controller_worker.sh /start.sh

ADD circe/{pricing_option}/monitor.py /centralized_scheduler/monitor.py


RUN chmod +x /start.sh

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]

"""

############################################ DOCKER GENERATORS #########################################################

template_computing_worker ="""\
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
ADD circe/{pricing_option}/requirements.txt /requirements.txt

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
RUN mkdir -p /home/darpa/apps/data

# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD {app_file}/scripts/ /centralized_scheduler/

ADD jupiter_config.ini /jupiter_config.ini
ADD jupiter_config.py /jupiter_config.py

ADD circe/{pricing_option}/start_computing_worker.sh /start.sh
ADD mulhome_scripts/keep_alive.py /centralized_scheduler/keep_alive.py
ADD {app_file}/configuration.txt  /centralized_scheduler/dag.txt
ADD {app_file}/scripts/config.json /centralized_scheduler/config.json
ADD {app_file}/sample_input/1botnet.ipsum /centralized_scheduler/1botnet.ipsum
ADD nodes.txt /centralized_scheduler/nodes.txt

ADD circe/{pricing_option}/compute.py /centralized_scheduler/compute.py
ADD circe/{pricing_option}/readconfig.py /readconfig.py
ADD {app_file}/name_convert.txt /centralized_scheduler/name_convert.txt

RUN chmod +x /start.sh

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]

"""

############################################ DOCKER GENERATORS #########################################################

template_nondag ="""\
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
ADD circe/{pricing_option}/requirements.txt /requirements.txt

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
ADD circe/{pricing_option}/monitor_nondag.py /centralized_scheduler/monitor.py
ADD circe/{pricing_option}/readconfig.py /readconfig.py
RUN mkdir -p /home/darpa/apps/data

# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE

ADD {app_file}/scripts/ /centralized_scheduler/
ADD {app_file}/configuration.txt  /centralized_scheduler/dag.txt
ADD {app_file}/sample_input/ /centralized_scheduler/sample_input/
ADD {app_file}/name_convert.txt /centralized_scheduler/name_convert.txt

ADD jupiter_config.ini /jupiter_config.ini


ADD circe/{pricing_option}/start_controller_nondag.sh /start.sh
RUN chmod +x /start.sh

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]

"""

############################################ DOCKER GENERATORS #########################################################


template_nondag_worker ="""\
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
ADD circe/{pricing_option}/requirements.txt /requirements.txt

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
ADD circe/{pricing_option}/monitor_nondag.py /centralized_scheduler/monitor.py
ADD circe/{pricing_option}/readconfig.py /readconfig.py


RUN mkdir -p /home/darpa/apps/data

# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD {app_file}/scripts/ /centralized_scheduler/
ADD {app_file}/configuration.txt  /centralized_scheduler/dag.txt
ADD {app_file}/sample_input/ /centralized_scheduler/sample_input/
ADD {app_file}/name_convert.txt /centralized_scheduler/name_convert.txt

ADD jupiter_config.ini /jupiter_config.ini


ADD circe/{pricing_option}/start_controller_nondag.sh /start.sh
RUN chmod +x /start.sh

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]
"""

############################################ HOME DOCKER TEMPLATE#########################################################

def write_circe_computing_worker_docker(**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    dfp = DockerfileParser(path='computing_worker_node.Dockerfile')
    dfp.content =template_computing_worker.format(**kwargs)
    # print(dfp.content)

def write_circe_controller_worker_docker(**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    dfp = DockerfileParser(path='controller_worker_node.Dockerfile')
    dfp.content =template_controller_worker.format(**kwargs)
    # print(dfp.content)


def write_circe_home_docker(**kwargs):
    """
        Function to Generate the Dockerfile of the home/master node of CIRCE
    """
    dfp = DockerfileParser(path='home_node.Dockerfile')
    dfp.content =template_home.format(**kwargs)

def write_circe_controller_nondag(**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    dfp = DockerfileParser(path='controller_nondag_node.Dockerfile')
    dfp.content =template_nondag.format(**kwargs)
    # print(dfp.content)

def write_circe_worker_nondag(**kwargs):
    """
      Function to Generate the Dockerfile of the worker nodes of Execution Profiler.
    """
    dfp = DockerfileParser(path='nondag_worker.Dockerfile')
    dfp.content =template_nondag_worker.format(**kwargs)
    # print(dfp.content)


if __name__ == '__main__':
    write_circe_home_docker(username = 'root',
                      password = 'PASSWORD',
                      app_file='app_specific_files/network_monitoring',
                      ports = '22 8888')

    write_circe_controller_worker_docker(username = 'root',
                      password = 'PASSWORD',
                      app_file='app_specific_files/network_monitoring',
                      ports = '22 57021')
    write_circe_computing_worker_docker(username = 'root',
                      password = 'PASSWORD',
                      app_file='app_specific_files/network_monitoring',
                      ports = '22 57021')
    write_circe_controller_nondag(username = 'root',
                      password = 'PASSWORD',
                      app_file='app_specific_files/network_monitoring',
                      ports = '22 8888')
