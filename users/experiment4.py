# Calculate overhead (number of messages) to compare WAVE greedy and HEFT
import os
import _thread
import shutil
from flask import Flask, request
import paho.mqtt.client as mqtt
import time

app = Flask(__name__)


class experience():
    def __init__(self,ID,subs,server,username,password, port,timeout,looptimeout,user_log):
        self.ID = ID
        self.subs = subs
        self.server = server
        self.port = port
        self.timeout = timeout
        self.looptimeout = looptimeout
        self.client = mqtt.Client(self.ID)
        self.username = username
        self.password = password
        self.client.username_pw_set(self.username,self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.server, self.port, self.timeout)
        self.user_log = user_log
        self.client.loop_forever()
        
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self,client, userdata, flags, rc):
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        subres = client.subscribe(self.subs,qos=1)
        print("Connected with result code "+str(rc))
        

    def on_message(self,client, userdata, msg):
        message = msg.payload.decode()
        print('--------------')
        print(message)
        print('--------------')
        with open(self.user_log,'a') as f:
            f.write(message)

def retrieve_nodes(node_file):
    print(node_file)
    f = open(node_file,'r')
    nodes =  []
    
    lines = f.readlines()
    for l in lines:
        nid = l.split(' ')[0]
        nodes.append(nid)
    f.close()

    return nodes

if __name__ == '__main__':

    global NODE_PATH,nodes
    
    SERVER_IP = "127.0.0.1"
    port = 1883
    timeout = 60
    

    NODE_PATH = '../nodes.txt'


    nodes = retrieve_nodes(NODE_PATH)

    folder = 'exp4'
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.mkdir(folder)

    for node in nodes:
        print(node)
        expname = 'dag30_%s.log'%(node)
        user_log ='%s/%s'%(folder,expname)
        topic = 'overhead_%s'%(node)
        _thread.start_new_thread(experience,(node,topic,SERVER_IP,'anrgusc','anrgusc',1883,400,1,user_log))
    app.run(host='0.0.0.0',port=5055)