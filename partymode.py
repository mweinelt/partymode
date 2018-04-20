#!/usr/bin/env python3

import os
from subprocess import run

import paho.mqtt.client as mqtt
import pyotp
from qrcode import QRCode

partymode_totp_secret = None
if os.path.exists('./secret'):
    # use existing secret
    with open('./secret') as handle:
        partymode_totp_secret = handle.read()
else:
    # generate new secret
    partymode_totp_secret = pyotp.random_base32()
    with open('./secret', 'w') as handle:
        handle.write(partymode_totp_secret)

partymode_totp = pyotp.TOTP(partymode_totp_secret)
partymode_enabled = False
topic_bell = "w17/door/bell/state"
topic_party_set = "w17/door/partymode/enabled/set"
topic_party_state = "w17/door/partymode/enabled"

# print provisioning qrcode to terminal
print("QRCode, usable with TOTP Application:")
qr = QRCode()
qr.add_data(partymode_totp.provisioning_uri('enable key', 'w17/door/partymode'))
qr.print_tty()

#connection with mqtt, to receive the bellstate
def on_connect(client, userdata, flags, rc):
    print("Verbunden mit mqtt.")
    client.subscribe(topic_bell)
    client.subscribe(topic_party_set)

#working with the message which has been delivered from the doorbell, running the summer
def on_message(client, userdata, msg):
    global partymode_enabled
    payload = msg.payload.decode()
    topic = msg.topic
    #print(topic, payload)
    if topic == topic_party_set:
        partymode_enabled = payload == partymode_totp.now()
        if partymode_enabled:
            print("Let's get ready to rumble!")
            client.publish(topic_party_state, payload=1)
        else:
            print("Bell functions as usually.")
            client.publish(topic_party_state, payload=0)
    if topic == topic_bell:
        if partymode_enabled and payload == "1":
            run("/door/wrapper_summer")
            print("Auf!")

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect("mqtt.w17.io", 1883)

client.loop_forever()
