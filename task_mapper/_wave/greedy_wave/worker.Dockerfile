FROM python:3.5

# Install required python libraries
ADD worker/requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

ARG port_expose=8888
EXPOSE $port_expose

RUN ls -la /
COPY worker/child_appointment_greedy.py /child_appointment.py
COPY worker/start.sh /
ADD jupiter_config.ini /jupiter_config.ini

WORKDIR /
RUN chmod +x /start.sh

CMD ["/start.sh"]

