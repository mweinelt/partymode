#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from subprocess import run

def on_connect(client, userdata, flags, rc):
    print("Verbunden mit mqtt.")
    client.subscribe("w17/door/bell/state")

def on_message(client, userdata, msg):
    if msg.payload.decode() == "1":
        print("Mach die Tür auf.")
        run("/door/wrapper_summer")

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect("mqtt.w17.io", 1883)

client.loop_forever()



