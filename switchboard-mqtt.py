from socketIO_client import SocketIO, BaseNamespace
from argparse import ArgumentParser, ArgumentTypeError
import paho.mqtt.client as mqtt
import yaml
import json
import logging
import threading
from sensormap import SensorMap

##
## cmd line argument parser
##

parser = ArgumentParser(description='switchboard-mqtt')
parser.add_argument(
    '-H',
    '--switchboard-host',
    action='store',
    dest='sio_addr',
    help='switchboard socket.io host address',
    type=str,
    default="127.0.0.1")
parser.add_argument(
    '-P',
    '--switchboard-port',
    action='store',
    dest='sio_port',
    help='switchboard socket.io port',
    type=int,
    default=9128)
parser.add_argument(
    '-q',
    '--mqtt-broker-host',
    action='store',
    dest='mqtt_addr',
    help='mqtt broker host address',
    type=str,
    default="127.0.0.1")
parser.add_argument(
    '-p',
    '--mqtt-broker-port',
    action='store',
    dest='mqtt_port',
    help='mqtt port port',
    type=int,
    default=1883)
parser.add_argument(
    '-c',
    '--mqtt-config',
    action='store',
    dest='mqtt_fname',
    help='mqtt config yaml file',
    type=str,
    default='conf/gateways.yml')

LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


def log_level_string_to_int(log_level_string):
    if not log_level_string in LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(
            log_level_string, LOG_LEVEL_STRINGS)
        raise ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the logging log_level_choices have not changed from our expected values
    assert isinstance(log_level_int, int)

    return log_level_int


parser.add_argument(
    '-l',
    '--log-level',
    action='store',
    dest='log_level',
    help='set the logging output level. {0}'.format(LOG_LEVEL_STRINGS),
    type=log_level_string_to_int,
    default='INFO')

pars = parser.parse_args()

##
## create logger
##

logger = logging.getLogger('switchboard-mqtt')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(pars.log_level)
formatter = logging.Formatter('%(levelname)s %(name)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

##
## connect Socket.IO
##

try:
    sio_client = SocketIO(
        pars.sio_addr,
        pars.sio_port,
        hurry_interval_in_seconds=10,
        wait_for_connection=False)
except:
    logger.error("can't connect to switchboard ({}:{})".format(
        pars.sio_addr, pars.sio_port))
    exit(1)

m = SensorMap()

#read config file and parse yaml to config_dict
with open(pars.mqtt_fname, 'r') as stream:
    try:
        config_dict = yaml.load(stream)
    except yaml.YAMLError as exc:
        logger.error(exc)
    m.add_gateways(config_dict)

##
## Socket.IO
##


class SensorsNamespace(BaseNamespace):
    '''class-based Socket.IO event handlers'''

    def on_actuator_response(self, *data):
        '''receive metrics of changed actuators, send it to MQTT'''

        logger.debug("on_actuator_response: {}".format(data))
        for node_id, node_data in json.loads(data[0]).items():
            for sensor_id, value in node_data.items():
                try:
                    topic_send = m.map_sensor2topic[node_id][sensor_id]
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
        m.setup_sensors(gw, data[0][gw])

    def on_status_response(self, *data):
        '''receive and log status message from switchboard'''

        logger.info("sio status response: {}".format(data))

    def on_connect(self):
        logger.debug("sio connect:")


sio_namespace = sio_client.define(SensorsNamespace, '/sensors')
m.join_gateways(sio_namespace)

##
## connect MQTT
##

mqtt_client = mqtt.Client()
try:
    mqtt_client.connect(pars.mqtt_addr, pars.mqtt_port, 60)
except:
    logger.error("can't connect to mqtt broker ({}:{})".format(
        pars.mqtt_addr, pars.mqtt_port))
    exit(1)

##
## MQTT
##


def on_connect(mqtt_client, userdata, flags, rc):
    logger.info("mqtt connected (status code {})".format(int(rc)))

    #after connect subscribe to MQTT topics
    m.subscribe_gateways(mqtt_client)


mqtt_client.on_connect = on_connect


def on_message(client, userdata, msg):
    '''receive message from MQTT, if there is metric from known sensor, send it to switchboard'''

    logger.debug("mqtt message: {} {}".format(msg.topic, msg.payload))

    metrics = {}

    for s in m.get_sensors(msg):
        logger.info("{}.{} = {}".format(s.node_id, s.sensor_id, s.value))

        if not s.node_id in metrics:
            metrics[s.node_id] = {}

        if not s.sensor_id in metrics[s.node_id]:
            metrics[s.node_id][s.sensor_id] = s.value

    sio_namespace.emit('sensor_response', metrics)


mqtt_client.on_message = on_message

##
## start server loops
##


def infiniteloop1():
    sio_client.wait()


def infiniteloop2():
    mqtt_client.loop_forever()


thread1 = threading.Thread(target=infiniteloop1)
thread1.start()

thread2 = threading.Thread(target=infiniteloop2)
thread2.start()
