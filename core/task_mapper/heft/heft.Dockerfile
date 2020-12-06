# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:18.04

# Install required libraries
RUN apt-get update
RUN apt-get -y install build-essential libssl-dev libffi-dev
RUN apt-get -yqq install python3.6 python3.6-dev python3-pip
RUN apt-get install -y openssh-server sshpass nano vim

# Authentication
RUN echo 'root:PASSWORD' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN service ssh restart

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Requirements for HEFT
ADD requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

# Prepare heft files
RUN mkdir -p /jupiter
ADD start.sh /jupiter/
ADD master_heft.py  /jupiter/
ADD heft.py /jupiter/
ADD create_input.py /jupiter/
ADD read_input_heft.py /jupiter/
ADD write_input_heft.py /jupiter/

RUN mkdir -p /jupiter/output
RUN chmod +x /jupiter/start.sh

# Add app specific files
ADD build/ /jupiter/build/

WORKDIR /jupiter

# kubernetes exposes ports for us
# EXPOSE

CMD ["./start.sh"]
