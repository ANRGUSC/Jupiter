# ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
# **     contributor: Pradipta Ghosh, Quynh Nguyen, Bhaskar Krishnamachari
# **     Read license file in main directory for more details

# Instructions copied from - https://hub.docker.com/_/python/
FROM anrg/rpi_netr_home:v0

RUN apt-get update && apt-get upgrade -y
# Install required libraries
RUN apt-get update
RUN apt-get -y install build-essential libssl-dev libffi-dev python-dev
RUN apt-get -yqq install python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y openssh-server sshpass nano virtualenv supervisor

# Install required python libraries
ADD profilers/network_resource_profiler/home/requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt


# Authentication
RUN echo 'root:PASSWORD' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

COPY mongo3-2 /usr/bin

# Prepare MongoDB
RUN mkdir -p /mongodb/data
RUN mkdir -p /mongodb/log
RUN mkdir -p /network_profiling

ADD profilers/network_resource_profiler/home/central_mongod /network_profiling/central_mongod

# Prepare network profiling code
ADD profilers/network_resource_profiler/home/central_input /network_profiling/central_input
ADD profilers/network_resource_profiler/home/central_query_statistics.py /network_profiling/central_query_statistics.py
ADD profilers/network_resource_profiler/home/central_scheduler.py /network_profiling/central_scheduler.py
ADD profilers/network_resource_profiler/home/generate_link_list.py /network_profiling/generate_link_list.py
ADD scripts/keep_alive.py /network_profiling/keep_alive.py


RUN mkdir -p /network_profiling/scheduling
RUN mkdir -p /network_profiling/parameters

# Prepare resource profiling code
RUN mkdir -p /resource_profiling
ADD profilers/network_resource_profiler/home/resource_profiling_files/ /resource_profiling/


# Running docker
ADD profilers/network_resource_profiler/home/start.sh /network_profiling/start.sh
RUN chmod +x /network_profiling/start.sh

ADD jupiter_config.ini /network_profiling/jupiter_config.ini

WORKDIR /network_profiling



# tell the port number the container should expose

EXPOSE 22 27017 8888

CMD ["./start.sh"]
