FROM ubuntu:18.04

RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev libssl-dev libffi-dev
RUN apt-get install -yqq openssh-client openssh-server wget net-tools sshpass
RUN apt-get install -y vim stress

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
RUN pip3 install -r /jupiter/requirements.txt

# add all jupiter application files and install any requirements
COPY build/app_specific_files/ /jupiter/app_specific_files/
RUN pip3 install -r /jupiter/app_specific_files/requirements.txt

# jupiter_utils library
COPY build/jupiter_utils/ /jupiter/jupiter_utils/

ADD profiler_worker.py /jupiter/profiler.py

ADD start_worker.sh /jupiter/start_worker.sh
ADD get_files.py /jupiter/get_files.py
ADD exec_profiler.py /jupiter/exec_profiler.py
ADD build/jupiter_config.ini /jupiter/jupiter_config.ini

RUN chmod +x /jupiter/start_worker.sh

WORKDIR /jupiter/

# Kubernetes handles exposing ports for us
# EXPOSE {ports}

CMD ["./start_worker.sh"]