# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:16.04

RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -y openssh-server mongodb
ADD simulation/demo_multiple_sources/requirements_data.txt /requirements.txt
RUN apt-get -y install build-essential libssl-dev libffi-dev python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y sshpass nano


RUN pip3 install -r requirements.txt
RUN echo 'root:PASSWORD' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile


# Add the task speficific configuration files
ADD app_specific_files/demo5/configuration.txt /configuration.txt

ADD nodes.txt /nodes.txt
ADD jupiter_config.ini /jupiter_config.ini

RUN mkdir generated_stream 
ADD simulation/demo_multiple_sources/start_home.sh /start.sh
ADD simulation/demo_multiple_sources/ds_stream.py /ds_stream.py
ADD simulation/demo_multiple_sources/data/tiger /data

RUN chmod +x /start.sh

WORKDIR /

# tell the port number the container should expose
EXPOSE 22 8888

# run the command
CMD ["./start.sh"]
