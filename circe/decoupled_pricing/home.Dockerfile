FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD circe/decoupled_pricing/requirements_home_controller.txt /requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY circe/decoupled_pricing/master_greedy.py /master.py

RUN mkdir -p DAG

COPY circe/decoupled_pricing/start_home_controller.sh /start.sh

ADD app_specific_files/dummy_app_multicast/configuration.txt DAG/DAG_application.txt
ADD app_specific_files/dummy_app_multicast/input_node.txt DAG
ADD app_specific_files/dummy_app_multicast/sample_input /

ADD jupiter_config.ini /jupiter_config.ini

EXPOSE 8888

RUN chmod +x /start.sh

WORKDIR /

CMD ["./start.sh"]
