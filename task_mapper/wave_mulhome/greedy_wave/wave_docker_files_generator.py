__author__ = "Quynh Nguyen and Bhaskar Krishnamachari"
__copyright__ = "Copyright (c) 2019, Autonomous Networks Research Group. All rights reserved."
__license__ = "GPL"
__version__ = "3.0"

from pprint import pprint
from dockerfile_parse import DockerfileParser

############################################ HOME DOCKER TEMPLATE #########################################################

template_home ="""\
FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD task_mapper/wave_mulhome/greedy_wave/home/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

COPY task_mapper/wave_mulhome/greedy_wave/home/master_greedy.py /master.py

RUN mkdir -p DAG

COPY task_mapper/wave_mulhome/greedy_wave/home/start.sh /

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

template_worker ="""\
FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD task_mapper/wave_mulhome/greedy_wave/worker/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

COPY task_mapper/wave_mulhome/greedy_wave/worker/child_appointment_greedy.py /child_appointment.py

RUN mkdir -p DAG

COPY task_mapper/wave_mulhome/greedy_wave/worker/start.sh /

ADD {app_file}/configuration.txt DAG/DAG_application.txt
ADD {app_file}/input_node.txt DAG
ADD {app_file}/sample_input /

ADD jupiter_config.ini /jupiter_config.ini


EXPOSE {ports}

RUN chmod +x /start.sh

WORKDIR /

CMD ["./start.sh"]
"""

############################################ DOCKER GENERATORS #########################################################


def write_wave_worker_docker(app_option=None,**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    if app_option==None:
        file_name = 'worker.Dockerfile'
    else:
        file_name = 'worker_%s.Dockerfile'%(app_option)
    dfp = DockerfileParser(path=file_name)
    dfp.content =template_worker.format(**kwargs)
    # print(dfp.content)
    return file_name
    

def write_wave_home_docker(app_option=None,**kwargs):
    """
        Function to Generate the Dockerfile of the worker nodes
    """
    if app_option==None:
        file_name = 'home.Dockerfile'
    else:
        file_name = 'home_%s.Dockerfile'%(app_option)
    dfp = DockerfileParser(path=file_name)
    dfp.content =template_home.format(**kwargs)
    # print(dfp.content)
    return file_name
    

if __name__ == '__main__':
    write_wave_worker_docker( app_file='app_specific_files/network_monitoring',
                      ports = '8888')
    write_wave_home_docker( app_file='app_specific_files/network_monitoring',
                      ports = '8888')
    
