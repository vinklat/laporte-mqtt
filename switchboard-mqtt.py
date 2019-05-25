from socketIO_client import SocketIO, BaseNamespace
from argparse import ArgumentParser, ArgumentTypeError
import paho.mqtt.client as mqtt
import yaml
import json
import logging
import time
import threading
from sensormap import SensorMap

# create logger
logger = logging.getLogger(__name__)

##
## cmd line argument parser
##

parser = ArgumentParser(description='MQTT connector for switchboard')
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
    help='mqtt broker port',
    type=int,
    default=1883)
parser.add_argument(
    '-k',
    '--mqtt-keepalive',
    action='store',
    dest='mqtt_keepalive',
    help='mqtt keepalive',
    type=int,
    default=30)
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
## set logger
##

logging.basicConfig(
    format='%(levelname)s %(module)s: %(message)s', level=pars.log_level)
logging.getLogger('urllib3').setLevel(logging.INFO)

##
## connect Socket.IO
##

try:
    sio_client = SocketIO(
        pars.sio_addr,
        pars.sio_port,
        hurry_interval_in_seconds=10,
        wait_for_connection=True)
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

    nconnects = 0

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
        self.nconnects += 1
        logger.debug("sio connected OK")

    def on_reconnect(self):
        self.nconnects += 1
        logger.debug("sio reconnected OK")

    def on_disconnect(self):
        logger.debug("sio disconnected")

    def on_error(self):
        logger.debug("sio error")


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
        m.subscribe_gateways(mqtt_client)
    else:
        logger.error("MQTT connect: code={}".format(rc))


def on_disconnect(client, userdata, rc):
    client.connected_flag = False
    logger.error("MQTT disconnect: code={}".format(rc))


def on_publish(client, userdata, mid):
    logger.debug("MQTT published: mid={}".format(mid))


def on_message(client, userdata, msg):
    '''receive message from MQTT, if there is metric from known sensor, send it to switchboard'''

    logger.debug("MQTT message: {} {}".format(msg.topic, msg.payload))

    metrics = {}

    for s in m.get_sensors(msg):
        logger.info("{}.{} = {}".format(s.node_id, s.sensor_id, s.value))

        if not s.node_id in metrics:
            metrics[s.node_id] = {}

        if not s.sensor_id in metrics[s.node_id]:
            metrics[s.node_id][s.sensor_id] = s.value

    if metrics:
        sio_namespace.emit('sensor_response', metrics)


mqtt.Client.connected_flag = False
mqtt_client = mqtt.Client(
    __file__ + '_{0:010x}'.format(int(time.time() * 256))[:10])
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_publish = on_publish
mqtt_client.on_message = on_message

##
## start server loops
##


def mqtt_loop():
    logger.info("conecting to mqtt broker ({}:{})".format(
        pars.mqtt_addr, pars.mqtt_port))

    try:
        mqtt_client.connect(pars.mqtt_addr, pars.mqtt_port,
                            pars.mqtt_keepalive)
    except:
        pass

    mqtt_client.loop_start()

    while True:
        while not mqtt_client.connected_flag:
            logger.debug("MQTT connect wait")
            time.sleep(10)


def sio_loop():
    last_nconnects = 0

    while True:
        if sio_namespace.nconnects > last_nconnects:
            m.join_gateways(sio_namespace)
            last_nconnects = sio_namespace.nconnects

        sio_client.wait(seconds=1)


##
## start server loops
##


def main():
    thread1 = threading.Thread(target=mqtt_loop)
    thread1.start()

    thread2 = threading.Thread(target=sio_loop)
    thread2.start()


if __name__ == '__main__':
    main()
