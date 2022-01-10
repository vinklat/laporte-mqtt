# -*- coding: utf-8 -*-
'''
Connect to Laporte Socket.IO
'''

import logging
import json
from laporte.client import LaporteClient
from laporte_mqtt.config import SCHEMA_JSON, SCHEMA_VALUE

logging.getLogger(__name__).addHandler(logging.NullHandler())


class Laporte(LaporteClient):
    '''
    Object containing Socket.IO client with registered namespaces.
    '''
    def publish_actuator(self, gateway, node_addr, keys):
        '''function launched upon an actuator response'''

        logging.info("Laporte receive: {'%s': %s}", node_addr, keys)
        if self.mqtt is None:
            logging.error("mqtt client not set")
            return

        gateway = self.mqtt.gateways.find_gateway(gateway)

        if gateway.subscribe_schema == SCHEMA_JSON:
            topic = gateway.publish_pattern.format(node_addr)
            payload = json.dumps(keys)
            logging.info("MQTT publish: %s %s", topic, payload)
            self.mqtt.publish(topic, payload)

        elif gateway.subscribe_schema == SCHEMA_VALUE:
            for key, value in keys.items():
                topic = gateway.publish_pattern.format(node_addr, key)
                logging.info("MQTT publish: %s %s", topic, value)
                self.mqtt.publish(topic, value)

    def __init__(self, addr: str, port: int, gateways: list = None) -> None:
        self.mqtt = None
        LaporteClient.__init__(self, addr, port, gateways=gateways)
        self.ns_metrics.actuator_addr_handler = self.publish_actuator
