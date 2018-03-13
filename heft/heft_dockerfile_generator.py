"""
 * Copyright (c) 2018, Autonomous Networks Research Group. All rights reserved.
 *     contributors:
 *      Pradipta Ghosh
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details
"""

from pprint import pprint
from dockerfile_parse import DockerfileParser

############################################ WORKER DOCKER #########################################################

template_heft ="""\
# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04

# Install required libraries
RUN apt-get update
RUN apt-get -y install build-essential libssl-dev libffi-dev python-dev
RUN apt-get -yqq install python python-pip python-dev python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y openssh-server sshpass nano virtualenv supervisor
RUN apt-get install -y vim

# Install required python libraries
ADD requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt
RUN pip2 install -r requirements.txt


# Authentication
RUN echo 'root:{PASSWORD}' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Prepare heft files
RUN mkdir -p heft
ADD start.sh /heft/start.sh
ADD keep_alive.py /heft/keep_alive.py
ADD master.py  /heft/master.py
ADD heft_dup.py /heft/heft_dup.py
ADD create_input.py /heft/create_input.py
ADD read_input_heft.py /heft/read_input_heft.py
ADD write_input_heft.py /heft/write_input_heft.py

#ADD input_0.tgff /heft/input_0.tgff

RUN mkdir -p /heft/output
RUN chmod +x /heft/start.sh
ADD dag.txt  /heft/dag.txt
ADD config.json /heft/config.json

WORKDIR /heft/


# tell the port number the container should expose
EXPOSE {ports}

CMD ["./start.sh"]
"""

############################################ DOCKER GENERATORS #########################################################

def write_heft_docker(**kwargs):
    dfp = DockerfileParser(path='Dockerfile')
    dfp.content =template_heft.format(**kwargs)
    # print(dfp.content)

if __name__ == '__main__':
    write_heft_docker(PASSWORD = 'PASSWORD',
                      ports = '22 5000')