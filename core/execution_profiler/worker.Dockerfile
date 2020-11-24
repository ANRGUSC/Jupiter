FROM ubuntu:18.04

# Install required libraries
RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get -yqq update
RUN apt-get install -yqq openssh-client openssh-server 
RUN apt-get install -yqq wget sshpass stress libgl1-mesa-glx

# Authentication
RUN echo 'root:PASSWORD' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN service ssh restart

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# install execution profiler requirements
ADD requirements.txt /jupiter/requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r /jupiter/requirements.txt

# install app specific requirements
COPY build_requirements/requirements.txt /jupiter/build/app_specific_files/
RUN pip3 install --upgrade pip
RUN pip3 install -r /jupiter/build/app_specific_files/requirements.txt

ADD profiler_worker.py /jupiter/profiler_worker.py

ADD start_worker.sh /jupiter/start_worker.sh
ADD remote_start.py /jupiter/remote_start.py
ADD utils.py /jupiter/utils.py

RUN chmod +x /jupiter/start_worker.sh

WORKDIR /jupiter/

# Add all files in the ./build/ folder. This folder is created by
# build_push_exec.py and contains copies of all files from Jupiter and the
# application. If you need to add more files, make the script copy files into
# ./build/ instead of adding it manually in this Dockerfile.
COPY build/ /jupiter/build/

# Kubernetes handles exposing ports for us
# EXPOSE

CMD ["./start_worker.sh"]