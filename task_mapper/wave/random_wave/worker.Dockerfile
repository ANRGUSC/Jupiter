FROM resin/armv7hf-debian

# Install required libraries
RUN apt-get update
RUN apt-get -y install build-essential libssl-dev libffi-dev python-dev
RUN apt-get -yqq install python python-pip python-dev python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y openssh-server sshpass nano virtualenv supervisor
RUN apt-get install -y vim

# Install required python libraries
ADD worker/requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

ARG port_expose=8888
EXPOSE $port_expose

RUN ls -la /
COPY worker/child_appointment_random.py /child_appointment.py
COPY worker/start.sh /

ADD jupiter_config.ini /jupiter_config.ini

WORKDIR /
RUN chmod +x /start.sh

CMD ["/start.sh"]

