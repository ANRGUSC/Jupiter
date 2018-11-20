FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD home/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

COPY home/master_greedy.py /master.py

RUN mkdir -p DAG
COPY app_specific_files/network_monitoring_app_dag/configuration.txt DAG/DAG_application.txt
COPY app_specific_files/network_monitoring_app_dag/input_node.txt DAG
ADD app_specific_files/network_monitoring_app_dag/sample_input/1botnet.ipsum /centralized_scheduler/1botnet.ipsum

RUN ls -la /

RUN ls -la DAG/

COPY home/start.sh /

RUN chmod +x /start.sh
ADD jupiter_config.ini /jupiter_config.ini

# ARG port_expose=8888
# EXPOSE $port_expose
EXPOSE 8888

WORKDIR /

CMD ["./start.sh"]
