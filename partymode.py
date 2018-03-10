#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from subprocess import run

partymode_enabled = False

#connection with mqtt, to receive the bellstate
def on_connect(client, userdata, flags, rc):
    print("Verbunden mit mqtt.")
    client.subscribe("w17/door/bell/state")
    client.subscribe("w17/door/partymode/enabled")

#working with the message which has been delivered from the doorbell, running the summer
def on_message(client, userdata, msg):
    global partymode_enabled
    payload = msg.payload.decode()
    topic = msg.topic
    #print(topic, payload)
    if topic == "w17/door/partymode/enabled":
        partymode_enabled = payload == "1"
        if partymode_enabled:
            print("Let's get ready to rumble!")
        else:
            print("Bell functions as usually.")
    if topic == "w17/door/bell/state":
        if partymode_enabled and payload == "1":
            run("/door/wrapper_summer")
            print("Auf!")

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect("mqtt.w17.io", 1883)

client.loop_forever()

