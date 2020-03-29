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
RUN apt-get install -yqq openssh-client openssh-server mongodb bzip2 wget net-tools sshpass screen
RUN apt-get install -y vim
RUN apt-get install g++ make openmpi-bin libopenmpi-dev -y
RUN apt-get install sudo -y
RUN apt-get install iproute2 -y

RUN apt-get install -y openssh-server

# Install required python libraries
ADD profilers/execution_profiler_mulhome/requirements.txt /requirements.txt

RUN pip3 install -r requirements.txt


# Authentication
RUN echo 'root:PASSWORD' | chpasswd
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

ADD profilers/execution_profiler_mulhome/central_mongod /central_mongod
RUN chmod +x /central_mongod


RUN mkdir -p /centralized_scheduler/profiler_files
RUN mkdir -p /centralized_scheduler/generated_files
RUN mkdir -p /centralized_scheduler/profiler_files_processed



# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD app_specific_files/sleep/scripts/ /centralized_scheduler/
COPY app_specific_files/sleep/sample_input /centralized_scheduler/sample_input
RUN mkdir -p /home/darpa/apps/data


ADD app_specific_files/sleep/configuration.txt /centralized_scheduler/DAG.txt
ADD nodes.txt /centralized_scheduler/nodes.txt

ADD profilers/execution_profiler_mulhome/start_home.sh /centralized_scheduler/start.sh
ADD mulhome_scripts/keep_alive.py /centralized_scheduler/keep_alive.py
ADD profilers/execution_profiler_mulhome/profiler_home.py /centralized_scheduler/profiler_home.py
ADD jupiter_config.ini /centralized_scheduler/jupiter_config.ini


WORKDIR /centralized_scheduler/
RUN ls
# Prepare scheduling files
RUN chmod +x /centralized_scheduler/start.sh


# tell the port number the container should expose
EXPOSE 22 27017 8888 57021

CMD ["./start.sh"]
