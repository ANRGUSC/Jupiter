FROM python:3.5
RUN pip install flask

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

COPY master.py /

RUN mkdir -p DAG
COPY DAG.txt DAG/DAG_application.txt
COPY input_node.txt DAG

RUN ls -la /

RUN ls -la DAG/

COPY start.sh /

RUN chmod +x /start.sh
EXPOSE 8080

WORKDIR /

CMD ["./start.sh"]