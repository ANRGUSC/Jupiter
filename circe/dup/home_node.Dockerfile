# Instructions copied from - https://hub.docker.com/_/python/
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

RUN pip3 --upgrade pip
RUN pip3 install -r requirements.txt
RUN echo 'root:PASSWORD' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Create the mongodb directories
RUN mkdir -p /mongodb/data
RUN mkdir -p /mongodb/log

# Create the input, output, and runtime profiler directories
RUN mkdir -p /input
RUN mkdir -p /output
#RUN mkdir -p /runtime


RUN apt-get install stress

# Add input files
COPY  app_specific_files/sleep/sample_input /sample_input

# Add the mongodb scripts
ADD circe/original/runtime_profiler_mongodb /central_mongod
#ADD circe/original/rt_profiler_update_mongo.py /run_update.py

ADD circe/original/readconfig.py /readconfig.py
ADD circe/original/scheduler.py /scheduler.py
ADD jupiter_config.py /jupiter_config.py
ADD circe/original/evaluate.py /evaluate.py


# Add the task speficific configuration files
ADD app_specific_files/sleep/configuration.txt /configuration.txt

ADD nodes.txt /nodes.txt
ADD jupiter_config.ini /jupiter_config.ini

ADD circe/original/start_home.sh /start.sh
RUN chmod +x /start.sh
RUN chmod +x /central_mongod

WORKDIR /

# tell the port number the container should expose
EXPOSE 22 8888

# run the command
CMD ["./start.sh"]
