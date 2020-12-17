FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

ADD requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

# Prepare wave files
RUN mkdir -p /jupiter
ADD start_home.sh /jupiter/start.sh
ADD master.py  /jupiter/

RUN mkdir -p /jupiter/output
RUN chmod +x /jupiter/start.sh

# Add app specific files
ADD build/ /jupiter/build/

WORKDIR /jupiter

# kubernetes exposes ports for us
# EXPOSE

CMD ["./start.sh"]
