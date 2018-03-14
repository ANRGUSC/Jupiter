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
RUN apt-get install -y openssh-server mongodb net-tools sshpass nano virtualenv supervisor

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
RUN mkdir -p /network_profiling
ADD droplet_mongod /network_profiling/droplet_mongod

# Prepare network profiling code
ADD droplet_generate_random_files /network_profiling/droplet_generate_random_files
ADD droplet_scp_time_transfer /network_profiling/droplet_scp_time_transfer
ADD automate_droplet.py /network_profiling/automate_droplet.py
ADD keep_alive.py /network_profiling/keep_alive.py

RUN mkdir -p /network_profiling/generated_test
RUN mkdir -p /network_profiling/received_test
RUN mkdir -p /network_profiling/scheduling


# Prepare resource profiling code
RUN mkdir -p /resource_profiler
ADD resource_profiler.py /resource_profiler/resource_profiler.py

#Running docker
ADD start.sh /network_profiling/start.sh
RUN chmod +x /network_profiling/start.sh



WORKDIR /network_profiling
# tell the port number the container should expose
EXPOSE 22
EXPOSE 8888
EXPOSE 27017

CMD ["./start.sh"]
