# Instructions copied from - https://hub.docker.com/_/python/
FROM ubuntu:18.04

RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get -yqq update
RUN apt-get install -yqq openssh-client openssh-server wget net-tools sshpass mongodb libgl1-mesa-glx rsyslog

# Authentication
RUN echo 'root:PASSWORD' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN service ssh restart

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# install CIRCE requirements
ADD requirements.txt /jupiter/requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r /jupiter/requirements.txt

# Create the input and output directories
RUN mkdir -p /jupiter/circe_input/
RUN mkdir -p /jupiter/circe_output/
ADD circe.py /jupiter/circe.py
ADD start.sh /jupiter/start.sh
RUN chmod +x /jupiter/start.sh

# install app specific requirements
COPY build_requirements/requirements.txt /jupiter/build/app_specific_files/
RUN pip3 install --upgrade pip
RUN pip3 install -r /jupiter/build/app_specific_files/requirements.txt

# Add all files in the ./build/ folder. This folder is created by
# build_push_circe.py and contains copies of all files from Jupiter and the
# application. If you need to add more files, make the script copy files into
# ./build/ instead of adding it manually in this Dockerfile.
COPY build/ /jupiter/build/

WORKDIR /jupiter/

# k8s will expose ports for us
# EXPOSE

# run the command
CMD ["./start.sh"]
