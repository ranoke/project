import paho.mqtt.client as mqtt
import json

# Configuration
broker_address = "mosquitto"  # Change this to your broker's IP address or hostname
broker_port = 1883
topic = "device/1234/status"
client_id = "your-client-id"

import sys

# Data to sen
status = bool(sys.argv[1])
power = int(sys.argv[2])

# Callback when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # After a successful connect, publish the message
    payload = json.dumps({"status": status, "power_usage": power})
    client.publish(topic, payload)

# Create an MQTT client instance
client = mqtt.Client(client_id)

# Assign callback functions
client.on_connect = on_connect

# Connect to the broker
client.connect(broker_address, broker_port, 60)

# Blocking call that handles reconnecting.
client.loop_forever()