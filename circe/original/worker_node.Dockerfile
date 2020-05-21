# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:18.04

RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get -yqq update
RUN apt-get install -y openssh-server mongodb
RUN apt-get -y install build-essential libssl-dev libffi-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y sshpass nano

# Chien's 2nd DAG
RUN apt-get install -y libsm6 libxext6 libxrender-dev

RUN pip3 install --upgrade pip
ADD circe/original/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

# RUN apt-get install -yqq openssh-client openssh-server sshpass
# RUN apt-get install g++ make openmpi-bin libopenmpi-dev -y
# RUN apt-get install sudo -y
# RUN apt-get install iproute2 -y

## Install TASK specific needs. The hadoop is a requirement for the network profiler application
##RUN wget http://supergsego.com/apache/hadoop/common/hadoop-2.8.1/hadoop-2.8.1.tar.gz -P ~/
#RUN wget https://archive.apache.org/dist/hadoop/core/hadoop-2.8.1/hadoop-2.8.1.tar.gz -P ~/
#RUN tar -zxvf ~/hadoop-2.8.1.tar.gz -C ~/
#RUN rm ~/hadoop-2.8.1.tar.gz

RUN apt-get -yqq update
RUN apt-get install -y mosquitto-clients

RUN echo 'root:PASSWORD' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile


RUN mkdir -p /centralized_scheduler/input
RUN mkdir -p /centralized_scheduler/output
RUN mkdir -p /centralized_scheduler/runtime
RUN mkdir -p /home/darpa/apps/data

#ADD circe/original/rt_profiler_data_update.py  /centralized_scheduler/rt_profiler_data_update.py

# IF YOU WANNA DEPLOY A DIFFERENT APPLICATION JUST CHANGE THIS LINE
ADD app_specific_files/demotest/scripts/ /centralized_scheduler/
ADD jupiter_config.ini /jupiter_config.ini
ADD circe/original/start_worker.sh /start.sh
RUN chmod +x /start.sh

ADD circe/original/monitor.py /centralized_scheduler/monitor.py

WORKDIR /

# tell the port number the container should expose
EXPOSE 22 57021

# run the command
CMD ["./start.sh"]

