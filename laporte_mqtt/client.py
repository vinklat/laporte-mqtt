# -*- coding: utf-8 -*-
# pylint: disable=C0411, C0412, C0413, C0103, E1101
'''client of Socket.IO laporte server and MQTT server'''

import json
import logging
import time
import threading
import re
import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Summary, Counter
from laporte.client import LaporteClient, c_connects_total
from laporte_mqtt.argparser import get_pars
from laporte_mqtt.config import GatewaysConfig, SCHEMA_JSON, SCHEMA_VALUE

# create logger
logger = logging.getLogger(__name__)

# Create a metric to track time spent and requests made.
MESSAGE_TIME = Summary('laporte_mqtt_message_seconds',
                       'Time spent processing MQTT message', [])

EMIT_COUNT = Counter('laporte_mqtt_emits_total', 'Total count of MQTT emits',
                     [])

# get parameters from command line arguments
pars = get_pars()

# set logger
logging.basicConfig(format='%(levelname)s %(module)s: %(message)s',
                    level=pars.log_level)
if pars.log_level == logging.DEBUG:
    logging.getLogger('socketio').setLevel(logging.DEBUG)
    logging.getLogger('engineio').setLevel(logging.DEBUG)
else:
    logging.getLogger('socketio').setLevel(logging.WARNING)
    logging.getLogger('engineio').setLevel(logging.WARNING)

# create cofiguration data container
gateways = GatewaysConfig(pars.gw_fname)

# define mqtt client and set client name
mqtt_client = mqtt.Client('laporte-mqtt_' +
                          '{0:010x}'.format(int(time.time() * 256))[:10])


def publish_actuator(gateway, node_addr, keys):
    '''function launched upon an actuator response'''

    logging.info("Laporte receive: {'%s': %s}", node_addr, keys)

    gateway = gateways.find_gateway(gateway)

    if gateway.subscribe_schema == SCHEMA_JSON:
        topic = gateway.publish_pattern.format(node_addr)
        payload = json.dumps(keys)
        logging.info("MQTT publish: %s %s", topic, payload)
        mqtt_client.publish(topic, payload)

    elif gateway.subscribe_schema == SCHEMA_VALUE:
        for key, value in keys.items():
            topic = gateway.publish_pattern.format(node_addr, key)
            logging.info("MQTT publish: %s %s", topic, value)
            mqtt_client.publish(topic, value)


laporte = LaporteClient(pars.sio_addr,
                        pars.sio_port,
                        gateways=list(gateways.get_names()))
laporte.ns_metrics.actuator_addr_handler = publish_actuator


def on_connect(client, userdata, flags, rc):
    '''
    fired upon a successful connection

    rc values:
    0: Connection successful
    1: Connection refused – incorrect protocol version
    2: Connection refused – invalid client identifier
    3: Connection refused – server unavailable
    4: Connection refused – bad username or password
    5: Connection refused – not authorised
    6-255: Currently unused.
    '''
    if rc == 0:
        client.connected_flag = True
        logger.info("MQTT connected OK")
        logger.debug("userdata=%s, flags=%s, rc=%s", userdata, flags, rc)

        # subscribe mqtt topics
        for gateway in gateways.get():
            logger.info("MQTT subscribe %s", gateway.subscribe_topic)
            mqtt_client.subscribe(gateway.subscribe_topic)

        # connects / reconnects counter
        c_connects_total.labels('mqtt').inc()
    else:
        logger.error("MQTT connect ERROR: code=%s", rc)


def on_disconnect(client, userdata, rc):
    '''fired upon a disconnection'''

    client.connected_flag = False
    logger.error("MQTT disconnect")
    logger.debug("userdata=%s, rc=%s", userdata, rc)


def on_publish(client, userdata, mid):
    '''fired upon a message published'''

    del client  # Ignored parameter
    EMIT_COUNT.inc()
    logger.debug("MQTT published: userdata=%s, mid=%s", userdata, mid)


@MESSAGE_TIME.time()
def on_message(client, userdata, msg):
    '''receive message from MQTT'''

    del client  # Ignored parameter
    logger.info("MQTT receive: %s %s", msg.topic, msg.payload)
    logger.debug("userdata=%s", userdata)

    for gateway in gateways.get():
        pattern = gateway.subscribe_pattern.format("(.*)", "(.*)")
        matchObj = re.match(r'{}'.format(pattern), msg.topic)
        if matchObj:
            groups = matchObj.groups()
            if (gateway.subscribe_schema == SCHEMA_JSON) and (
                    len(groups) == 1):
                node_addr = groups[0]
                message = {node_addr: json.loads(msg.payload)}
                break
            if (gateway.subscribe_schema == SCHEMA_VALUE) and (
                    len(groups) == 2):
                node_addr = groups[0]
                key = groups[1]
                message = {node_addr: {key: msg.payload.decode('ascii')}}
                break

    if matchObj:
        laporte.emit("sensor_addr_response", message)
    else:
        logger.warning("MQTT topic %s not match any gateway", msg.topic)


def mqtt_loop():
    '''main loop for MQTT client'''

    mqtt.Client.connected_flag = False
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_publish = on_publish
    mqtt_client.on_message = on_message

    logger.info("conecting to mqtt broker (%s:%s)", pars.mqtt_addr,
                pars.mqtt_port)

    mqtt_client.connect(pars.mqtt_addr, pars.mqtt_port, pars.mqtt_keepalive)
    mqtt_client.loop_start()

    while True:
        nattempts = 0
        while not mqtt_client.connected_flag:
            if nattempts > 0:
                logger.error("MQTT connect wait (attempt=%s)", nattempts)
            time.sleep(10)
            nattempts += 1
        time.sleep(1)


def main():
    '''start main loops'''

    # start up the server to expose promnetheus metrics.
    start_http_server(pars.port)

    thread1 = threading.Thread(target=mqtt_loop)
    thread1.start()

    thread2 = threading.Thread(target=laporte.loop)
    thread2.start()
