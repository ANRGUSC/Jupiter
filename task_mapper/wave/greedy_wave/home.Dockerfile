FROM resin/armv7hf-debian

# Install required libraries
RUN apt-get update
RUN apt-get -y install build-essential libssl-dev libffi-dev python-dev
RUN apt-get -yqq install python python-pip python-dev python3-pip python3-dev
RUN pip3 install --upgrade pip
RUN apt-get install -y openssh-server sshpass nano virtualenv supervisor
RUN apt-get install -y vim

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile
RUN pip install --upgrade pip
ADD home/requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

COPY home/master_greedy.py /master.py

RUN mkdir -p DAG
COPY DAG.txt DAG/DAG_application.txt
COPY input_node.txt DAG

RUN ls -la /

RUN ls -la DAG/

COPY home/start.sh /

RUN chmod +x /start.sh
ADD jupiter_config.ini /jupiter_config.ini

ARG port_expose=8888
EXPOSE $port_expose

WORKDIR /

CMD ["./start.sh"]