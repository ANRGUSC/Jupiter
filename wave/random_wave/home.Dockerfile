FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD home/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

COPY home/master.py /

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