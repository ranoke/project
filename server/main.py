import re
import json
from datetime import datetime
from paho.mqtt import client as mqtt_client
from pymongo import MongoClient

# MongoDB setup
mongo_client = MongoClient("mongodb://mongoadmin:secret@mongo:27017/")
db = mongo_client["device_data"]
collection = db["power_consumption"]

# MQTT details
broker = 'mosquitto'
port = 1883
topic = "device/+/status"  # Subscribing to all device statuses

# The client ID can be anything unique
client_id = 'python-mqtt-server'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        data = json.loads(msg.payload.decode())
        process_message(msg.topic, data)

    client.subscribe(topic)
    client.on_message = on_message

def get_device_id(topic):
    pattern = r"device\/(.+)\/status"
    match = re.search(pattern, topic)
    if match:
        return match.group(1)
    else:
        return None

def process_message(topic, data):
    data['timestamp'] = datetime.utcnow()
    data['device_id'] = get_device_id(topic)
    del data['status']
    collection.insert_one(data)

def publish(client, topic, msg):
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

def run():
    # while True:
    #     pass
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

if __name__ == '__main__':
    run()