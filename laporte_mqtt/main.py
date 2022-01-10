# -*- coding: utf-8 -*-
'''
MQTT bridge for Laporte
'''

import threading
from prometheus_client import start_http_server
from laporte_mqtt.logger import logger
from laporte_mqtt.argparser import pars
from laporte_mqtt.version import app_instance
from laporte_mqtt.config import GatewaysConfig
from laporte_mqtt.mqtt import Mqqt, MqttException
from laporte_mqtt.laporte import Laporte


def main():
    '''
    start main loops
    '''

    logger.info("Start %s...", app_instance)

    # create cofiguration data container
    gateways = GatewaysConfig(pars.config_file)

    # create laporte client
    laporte = Laporte(pars.laporte_host,
                      pars.laporte_port,
                      gateways=list(gateways.get_names()))

    # create mqtt client
    mqtt = Mqqt(gateways, laporte)
    laporte.mqtt = mqtt

    try:
        mqtt.connect(
            pars.mqtt_broker_host,
            pars.mqtt_broker_port,
            keepalive=pars.mqtt_keepalive,
        )
    except MqttException as exc:
        logger.critical(exc)
        return

    # start up the server to expose promnetheus metrics.
    start_http_server(pars.listen_port, addr=pars.listen_addr)

    # start MQTT loop
    thread1 = threading.Thread(target=mqtt.loop)
    thread1.start()

    # start Socket.IO loop
    thread2 = threading.Thread(target=laporte.loop)
    thread2.start()
