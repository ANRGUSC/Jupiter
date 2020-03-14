__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

from pprint import pprint
from dockerfile_parse import DockerfileParser

############################################ HOME DOCKER TEMPLATE #########################################################

template_home_controller ="""\
FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD circe/{pricing_option}/requirements_home_controller.txt /requirements.txt
RUN pip3 install -r requirements.txt

COPY circe/{pricing_option}/master_greedy.py /master.py

RUN mkdir -p DAG

COPY circe/{pricing_option}/start_home_controller.sh /start.sh

ADD {app_file}/configuration.txt DAG/DAG_application.txt
ADD {app_file}/input_node.txt DAG
ADD {app_file}/sample_input /

ADD jupiter_config.ini /jupiter_config.ini

EXPOSE {ports}

RUN chmod +x /start.sh

WORKDIR /

CMD ["./start.sh"]
"""



############################################ WORKER DOCKER TEMPLATE#########################################################

template_worker_controller ="""\
FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD circe/{pricing_option}/requirements_worker_controller.txt /requirements.txt
RUN pip3 install -r requirements.txt

COPY circe/{pricing_option}/child_appointment_greedy.py /child_appointment.py

RUN mkdir -p DAG

COPY circe/{pricing_option}/start_worker_controller.sh /start.sh

ADD {app_file}/configuration.txt DAG/DAG_application.txt
ADD {app_file}/input_node.txt DAG
# ADD {app_file}/sample_input/1botnet.ipsum /1botnet.ipsum
ADD {app_file}/sample_input /

ADD jupiter_config.ini /jupiter_config.ini


EXPOSE {ports}

RUN chmod +x /start.sh

WORKDIR /

CMD ["./start.sh"]
"""

############################################ DOCKER GENERATORS #########################################################


def write_decoupled_pricing_controller_worker_docker(app_option=None,**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    if app_option==None:
        file_name = 'worker.Dockerfile'
    else:
        file_name = 'worker_%s.Dockerfile'%(app_option)
    dfp = DockerfileParser(path=file_name)
    dfp.content =template_worker_controller.format(**kwargs)
    # print(dfp.content)
    return file_name
    

def write_decoupled_pricing_controller_home_docker(app_option=None,**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    if app_option==None:
        file_name = 'home.Dockerfile'
    else:
        file_name = 'home_%s.Dockerfile'%(app_option)
    dfp = DockerfileParser(path=file_name)
    dfp.content =template_home_controller.format(**kwargs)
    # print(file_name)
    # print(dfp.content)
    return file_name
    

template_home_compute ="""\
# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04
RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -y openssh-server mongodb
ADD circe/{pricing_option}/requirements_compute.txt /requirements.txt
RUN apt-get -y install build-essential libssl-dev libffi-dev python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y sshpass nano

# Taken from quynh's network profiler
RUN pip install cryptography

RUN apt-get -yqq update
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

ADD circe/{pricing_option}/start_home_compute.sh /start.sh
RUN chmod +x /start.sh
RUN chmod +x /central_mongod
ADD {app_file}/name_convert.txt /centralized_scheduler/name_convert.txt
ADD {app_file}/sample_input/1botnet.ipsum /centralized_scheduler/1botnet.ipsum
ADD {app_file}/scripts/config.json /centralized_scheduler/config.json
ADD {app_file}/configuration.txt  /centralized_scheduler/dag.txt

WORKDIR /

# tell the port number the container should expose
EXPOSE {ports}

# run the command
CMD ["./start.sh"]
"""

############################################ DOCKER GENERATORS #########################################################

template_worker_compute ="""\
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
ADD circe/{pricing_option}/requirements_compute.txt /requirements.txt

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

ADD circe/{pricing_option}/start_worker_compute.sh /start.sh
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

def write_decoupled_pricing_circe_compute_worker_docker(**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    dfp = DockerfileParser(path='worker_compute.Dockerfile')
    dfp.content =template_worker_compute.format(**kwargs)

def write_decoupled_pricing_circe_compute_home_docker(**kwargs):
    """
        Function to Generate the Dockerfile of the home/master node of CIRCE
    """
    dfp = DockerfileParser(path='home_compute.Dockerfile')
    dfp.content =template_home_compute.format(**kwargs)