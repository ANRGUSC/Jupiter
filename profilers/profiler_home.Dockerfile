# ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
# **     contributor: Pradipta Ghosh, Quynh Nguyen, Bhaskar Krishnamachari
# **     Read license file in main directory for more details

# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04

# Install required libraries
RUN apt-get update
RUN apt-get -y install build-essential libssl-dev libffi-dev python-dev
RUN apt-get -yqq install python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y openssh-server mongodb sshpass nano virtualenv supervisor

# Install required python libraries
ADD profilers/home/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt


# Authentication
RUN echo 'root:PASSWORD' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Prepare MongoDB
RUN mkdir -p /mongodb/data
RUN mkdir -p /mongodb/log
RUN mkdir -p /network_profiling

ADD profilers/home/central_mongod /network_profiling/central_mongod

# Prepare network profiling code
ADD profilers/home/central_input /network_profiling/central_input
ADD profilers/home/central_query_statistics.py /network_profiling/central_query_statistics.py
ADD profilers/home/central_scheduler.py /network_profiling/central_scheduler.py
ADD profilers/home/generate_link_list.py /network_profiling/generate_link_list.py


RUN mkdir -p /network_profiling/scheduling
RUN mkdir -p /network_profiling/parameters

# Prepare resource profiling code
RUN mkdir -p /resource_profiling
ADD profilers/home/resource_profiling_files/ /resource_profiling/


# Running docker
ADD profilers/home/start.sh /network_profiling/start.sh
RUN chmod +x /network_profiling/start.sh

ADD jupiter_config.ini /network_profiling/jupiter_config.ini

WORKDIR /network_profiling



# tell the port number the container should expose

EXPOSE 22 27017 8888

CMD ["./start.sh"]
