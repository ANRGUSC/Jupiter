FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD task_mapper/wave_mulhome/random_wave/home/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

COPY task_mapper/wave_mulhome/random_wave/home/master_random.py /master.py

RUN mkdir -p DAG

COPY task_mapper/wave_mulhome/random_wave/home/start.sh /

ADD app_specific_files/network_monitoring_app/configuration.txt DAG/DAG_application.txt
ADD app_specific_files/network_monitoring_app/input_node.txt DAG

ADD jupiter_config.ini /jupiter_config.ini

EXPOSE 8888

RUN chmod +x /start.sh

WORKDIR /

CMD ["./start.sh"]
