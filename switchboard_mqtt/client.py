# -*- coding: utf-8 -*-
'''threaded client of Socket.IO switchboard server and MQTT server'''

import yaml
import json
import logging
import time
import threading
import paho.mqtt.client as mqtt
from socketIO_client import SocketIO, BaseNamespace
from switchboard_mqtt.argparser import get_pars
from switchboard_mqtt.sensormap import SensorMap

# create logger
logger = logging.getLogger(__name__)

# get parameters from command line arguments
pars = get_pars()

# set logger
logging.basicConfig(format='%(levelname)s %(module)s: %(message)s',
                    level=pars.log_level)
logging.getLogger('urllib3').setLevel(logging.INFO)

# create cofiguration data container
sensor_map = SensorMap()

# define mqtt client and set client name
mqtt_client = mqtt.Client(__file__ +
                          '_{0:010x}'.format(int(time.time() * 256))[:10])


class SensorsNamespace(BaseNamespace):
    '''class-based Socket.IO event handlers'''

    nconnects = 0

    def on_actuator_response(self, *data):
        '''receive metrics of changed actuators, send it to MQTT'''

        logger.debug("on_actuator_response: {}".format(data))
        for node_id, node_data in json.loads(data[0]).items():
            for sensor_id, value in node_data.items():
                try:
                    topic_send = sensor_map.map_sensor2topic[node_id][
                        sensor_id]
                except KeyError:
                    logger.error("addr/key not configured! ({}.{})".format(
                        node_id, sensor_id))
                    continue

                logger.info("MQTT message to {} ({}.{}): {}".format(
                    topic_send, node_id, sensor_id, value))
                mqtt_client.publish(topic_send, value)

    def on_config_response(self, *data):
        '''receive sensor configuration from switchboard (after room join)'''

        gw = next(iter(data[0]))
        logger.debug("{} config response from switchboard:".format(gw))
        sensor_map.setup_sensors(gw, data[0][gw])

    def on_status_response(self, *data):
        '''receive and log status message from switchboard'''

        logger.info("sio status response: {}".format(data))

    def on_connect(self):
        self.nconnects += 1
        logger.debug("sio connected OK")

    def on_reconnect(self):
        self.nconnects += 1
        logger.debug("sio reconnected OK")

    def on_disconnect(self):
        logger.debug("sio disconnected")

    def on_error(self):
        logger.debug("sio error")


def sio_connect():
    '''connect to switchboard server'''

    try:
        sio_client = SocketIO(pars.sio_addr,
                              pars.sio_port,
                              hurry_interval_in_seconds=10,
                              wait_for_connection=True)
    except:
        logger.error("can't connect to switchboard ({}:{})".format(
            pars.sio_addr, pars.sio_port))
        exit(1)

    return sio_client


def get_config():
    '''read config file and parse yaml to config_dict'''

    try:
        with open(pars.mqtt_fname, 'r') as stream:
            try:
                config_dict = yaml.load(stream)
            except yaml.YAMLError as exc:
                logger.error(exc)
                exit(1)
        return config_dict
    except FileNotFoundError as exc:
        logger.critical(exc)
        exit(1)


# read config file and fill sensor map container
sensor_map.add_gateways(get_config())

# create Socket.IO client
sio_client = sio_connect()
sio_namespace = sio_client.define(SensorsNamespace, '/sensors')


def on_connect(client, userdata, flags, rc):
    '''
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
        #after connect subscribe to MQTT topics
        sensor_map.subscribe_gateways(mqtt_client)
    else:
        logger.error("MQTT connect ERROR: code={}".format(rc))


def on_disconnect(client, userdata, rc):
    client.connected_flag = False
    logger.error("MQTT disconnect: code={}".format(rc))


def on_publish(client, userdata, mid):
    logger.debug("MQTT published: mid={}".format(mid))


def on_message(client, userdata, msg):
    '''receive message from MQTT, if there is metric from known sensor, send it to switchboard'''

    logger.debug("MQTT message: {} {}".format(msg.topic, msg.payload))

    metrics = {}

    for s in sensor_map.get_sensors(msg):
        logger.info("{}.{} = {}".format(s.node_id, s.sensor_id, s.value))

        if not s.node_id in metrics:
            metrics[s.node_id] = {}

        if not s.sensor_id in metrics[s.node_id]:
            metrics[s.node_id][s.sensor_id] = s.value

    if metrics:
        sio_namespace.emit('sensor_response', metrics)


def mqtt_loop():
    '''main loop for MQTT client'''

    mqtt.Client.connected_flag = False
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_publish = on_publish
    mqtt_client.on_message = on_message

    logger.info("conecting to mqtt broker ({}:{})".format(
        pars.mqtt_addr, pars.mqtt_port))

    try:
        mqtt_client.connect(pars.mqtt_addr, pars.mqtt_port,
                            pars.mqtt_keepalive)
    except:
        pass

    mqtt_client.loop_start()

    while True:
        nattempts = 0
        while not mqtt_client.connected_flag:
            if nattempts > 0:
                logger.error(
                    "MQTT connect wait (attempt={})".format(nattempts))
            time.sleep(10)
            nattempts += 1
        time.sleep(1)


def sio_loop():
    '''main loop for Socket.IO client'''

    last_nconnects = 0

    while True:
        if sio_namespace.nconnects > last_nconnects:
            sensor_map.join_gateways(sio_namespace)
            last_nconnects = sio_namespace.nconnects

        sio_client.wait(seconds=1)


def main():
    '''start main loops'''

    thread1 = threading.Thread(target=mqtt_loop)
    thread1.start()

    thread2 = threading.Thread(target=sio_loop)
    thread2.start()
