FROM python:3.5

# Install required python libraries
ADD requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

EXPOSE 8080

RUN ls -la /
COPY child_appointment.py /
COPY start.sh /
WORKDIR /
RUN chmod +x /start.sh

CMD ["/start.sh"]

