#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "2.1"

from pprint import pprint
from dockerfile_parse import DockerfileParser

############################################ WORKER DOCKER TEMPLATE #########################################################

template_sim ="""\
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


RUN pip3 install -r requirements.txt
RUN echo '{username}:{password}' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

RUN apt-get install stress

ADD simulation/requirements.txt /requirements.txt

RUN pip3 install -r requirements.txt

ADD jupiter_config.ini /jupiter_config.ini
ADD simulation/stress_test.py /stress_test.py
ADD simulation/cpu_test.py /cpu_test.py
ADD simulation/start_home.sh /start.sh
RUN chmod +x /start.sh


WORKDIR /

EXPOSE {ports}

CMD ["./start.sh"]"""

def write_sim_docker(**kwargs):
	"""
			Function to Generate the Dockerfile of HEFT
	"""
	dfp = DockerfileParser(path='sim.Dockerfile')
	dfp.content =template_sim.format(**kwargs)
	# print(dfp.content)
if __name__ == '__main__':
		write_sim_docker(username = 'root',
											password = 'PASSWORD',
											ports = '22 8888')