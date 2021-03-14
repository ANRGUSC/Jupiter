# ** Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
# **     contributor: Pradipta Ghosh, Quynh Nguyen, Bhaskar Krishnamachari
# **     Read license file in main directory for more details

# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04

# Install required libraries
RUN apt-get update
RUN apt-get -y install build-essential libssl-dev libffi-dev python-dev
RUN apt-get -yqq install python3-pip python3-dev
RUN pip3 install --upgrade "pip < 21.0"
RUN apt-get update
RUN apt-get install -y openssh-server mongodb sshpass nano virtualenv supervisor

# Install required python libraries
ADD requirements.txt /requirements.txt
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
RUN mkdir -p /jupiter
ADD mongod /jupiter/central_mongod
RUN chmod +x /jupiter/central_mongod

# Add all files in the ./build/ folder. This folder is created by
# build_push_exec.py and contains copies of all files from Jupiter and the
# application. If you need to add more files, make the script copy files into
# ./build/ instead of adding it manually in this Dockerfile.
COPY build/ /jupiter/build/

# Prepare network profiling code
ADD central_input /jupiter/central_input
ADD central_scheduler.py /jupiter/central_scheduler.py
ADD generate_link_list.py /jupiter/generate_link_list.py
ADD keep_alive.py /jupiter/keep_alive.py

RUN mkdir -p /jupiter/scheduling
RUN mkdir -p /jupiter/parameters
RUN mkdir -p /jupiter/generated_test
RUN mkdir -p /jupiter/received_test


# Prepare network profiling code
ADD droplet_generate_random_files /jupiter/droplet_generate_random_files
ADD droplet_scp_time_transfer /jupiter/droplet_scp_time_transfer
RUN chmod +x /jupiter/droplet_scp_time_transfer
RUN chmod +x /jupiter/droplet_generate_random_files

# Running docker
ADD start_home.sh /jupiter/start.sh
RUN chmod +x /jupiter/start.sh

WORKDIR /jupiter

# k8s exposes ports for us
# EXPOSE 22 27017 8888

CMD ["./start.sh"]
