import paho.mqtt.client as mqtt 
import time

def onDisconnect(client, userdata, rc):
  print("disonnected")

def onConnect(client, userdata, rc):
  print("connected")

mqttc=mqtt.Client("publisher")
mqttc.on_connect = onConnect
mqttc.on_disconnect = onDisconnect
mqttc.connect("127.0.0.1", port=1883, keepalive=60)
mqttc.loop_start()
while True:
  mqttc.publish("test","Hello")
  time.sleep(10)# sleep for 10 seconds before next call