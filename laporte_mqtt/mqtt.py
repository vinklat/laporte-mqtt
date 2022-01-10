# -*- coding: utf-8 -*-
'''
Connect to a MQTT broker
'''

import re
import logging
import time
import json
from socket import gaierror
import paho.mqtt.client as mqtt
from laporte_mqtt.version import app_instance
from laporte_mqtt.metrics import mqtt_message_time, mqtt_emits_total, mqtt_connects_total
from laporte_mqtt.config import GatewaysConfig, SCHEMA_JSON, SCHEMA_VALUE
from laporte_mqtt.laporte import Laporte

# create logger
logging.getLogger(__name__).addHandler(logging.NullHandler())


class MqttException(Exception):
    def __init__(self, message):
        Exception.__init__(self, f'MQTT: {message}')


class Mqqt():
    def __init__(self, gateways: GatewaysConfig, laporte: Laporte) -> None:
        self.client = mqtt.Client(app_instance)
        self.client.connected_flag = False
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.gateways = gateways
        self.laporte = laporte

    def connect(self, host: str, port: int, keepalive=30):
        try:
            self.client.connect(host, port, keepalive)
        except (ConnectionRefusedError, OSError, gaierror) as exc:
            raise MqttException(exc) from exc

    def is_connected(self):
        return self.client.connected_flag

    def on_connect(self, _, userdata, flags, ret):
        '''
        fired upon a successful connection

        ret values:
        0: Connection successful
        1: Connection refused - incorrect protocol version
        2: Connection refused - invalid client identifier
        3: Connection refused - server unavailable
        4: Connection refused - bad username or password
        5: Connection refused - not authorised
        6-255: Currently unused.
        '''

        if ret == 0:
            self.client.connected_flag = True
            logging.info("MQTT connected OK")
            logging.debug("userdata=%s, flags=%s, ret=%s", userdata, flags, ret)

            # subscribe mqtt topics
            for gateway in self.gateways.get():
                logging.info("MQTT subscribe %s", gateway.subscribe_topic)
                self.client.subscribe(gateway.subscribe_topic)

            # connects / reconnects counter
            mqtt_connects_total.inc()
        else:
            logging.error("MQTT connect ERROR: ret=%s", ret)

    def on_disconnect(self, _, userdata, ret):
        '''fired upon a disconnection'''

        self.client.connected_flag = False
        logging.error("MQTT disconnect")
        logging.debug("userdata=%s, ret=%s", userdata, ret)

    def on_publish(self, client, userdata, mid):
        '''fired upon a message published'''

        del client  # Ignored parameter
        mqtt_emits_total.inc()
        logging.debug("MQTT published: userdata=%s, mid=%s", userdata, mid)

    @mqtt_message_time.time()
    def on_message(self, client, userdata, msg):
        '''receive message from MQTT'''

        del client  # Ignored parameter
        logging.info("MQTT receive: %s %s", msg.topic, msg.payload)
        logging.debug("userdata=%s", userdata)

        for gateway in self.gateways.get():
            pattern = gateway.subscribe_pattern.format("(.*)", "(.*)")
            match_obj = re.match(pattern, msg.topic)
            if match_obj:
                groups = match_obj.groups()
                if (gateway.subscribe_schema == SCHEMA_JSON) and (len(groups) == 1):
                    node_addr = groups[0]
                    message = {node_addr: json.loads(msg.payload)}
                    break
                if (gateway.subscribe_schema == SCHEMA_VALUE) and (len(groups) == 2):
                    node_addr = groups[0]
                    key = groups[1]
                    message = {node_addr: {key: msg.payload.decode('ascii')}}
                    break

        if match_obj:
            self.laporte.emit("sensor_addr_response", message)
        else:
            logging.warning("MQTT topic %s not match any gateway", msg.topic)

    def loop(self):
        self.client.loop_start()

        while True:
            nattempts = 0
            while not self.is_connected():
                if nattempts > 0:
                    logging.error("MQTT connect wait... (attempt=%s)", nattempts)
                time.sleep(10)
                nattempts += 1
            time.sleep(1)

    def publish(self, topic, payload):
        logging.info("MQTT publish: %s %s", topic, payload)
        self.client.publish(topic, payload)
