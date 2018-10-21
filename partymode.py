#!/usr/bin/env python3

import os
from subprocess import run
from datetime import date

import paho.mqtt.client as mqtt
import pyotp
from qrcode import QRCode
import yaml
import sys

partymode_totp_secret = None
if os.path.exists('./secret'):
    # use existing secret
    with open('./secret', encoding='UTF-8') as handle:
        partymode_totp_secret = handle.read()
else:
    # generate new secret
    partymode_totp_secret = pyotp.random_base32()
    with open('./secret', 'w') as handle:
        handle.write(partymode_totp_secret)

try:
    with open("config.yml") as handle:
        config = yaml.load(handle)
except FileNotFoundError:
    print("cannot find config.yml, please copy and modify config.yml.example", file=sys.stderr)
    sys.exit(1)

partymode_totp = pyotp.TOTP(partymode_totp_secret)
partymode_enabled = False
partymode_enabled_date = None
topic_bell = config["topic_bell"]
topic_party_set = config["topic_party_set"]
topic_party_state = config["topic_party_state"]
topic_door_lock_state = config["topic_door_lock_state"]

# print provisioning qrcode to terminal
print("QRCode, usable with TOTP Application:")
qr = QRCode()
qr.add_data(partymode_totp.provisioning_uri('enable key', 'w17/door/partymode'))
qr.print_tty()

# connection with mqtt broker, subscribe to updates for several states
def on_connect(client, userdata, flags, rc):
    print("Verbunden mit mqtt.")
    client.publish(topic_party_state, payload=1 if partymode_enabled else 0)
    client.subscribe([
        (topic_bell, 0),  # Does the bell ring?
        (topic_party_set, 0),  # Does somebody try to en/disable the partymode?
        (topic_door_lock_state, 0)  # Is the door locked?
    ])

# receive updates from mqtt broker
def on_message(client, userdata, msg):
    global partymode_enabled

    # Read topic and payload from message
    # payload is the value of the message
    # topic describes what has changed
    payload = msg.payload.decode()
    topic = msg.topic

    # Decision, which codepath will be used, depending on the topic
    if topic == topic_party_set:
        switch_partymode(
            enable=payload == partymode_totp.now(),
            client=client
        )
    elif topic == topic_bell:
        if not partymode_enabled:
            return

        if payload == "1":
            if date.today() > partymode_enabled_date:
                switch_partymode(
                    enable=False,
                    client=client
                )
                print("The day has changed. Therefore, the door now works as "
                      "usual and the partymode has been disabled.")
                return

            run("/door/wrapper_summer")
            print("Auf!")
    elif topic == topic_door_lock_state:
        # Door is locked.
        if payload == "1":
            switch_partymode(
                enable=False,
                client=client
            )

def switch_partymode(enable, client):
    global partymode_enabled, partymode_enabled_date
    partymode_enabled = enable

    if enable:
        print("Let's get ready to rumble!")
        client.publish(topic_party_state, payload=1)
        partymode_enabled_date = date.today()
    else:
        print("Bell functions as usually.")
        client.publish(topic_party_state, payload=0)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(config["mqtt_host"], config["mqtt_port"])

client.loop_forever()
