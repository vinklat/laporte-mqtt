import json
import logging

# create logger
logging.getLogger(__name__).addHandler(logging.NullHandler())


class Gateway():
    '''container to store mqtt prefixes configuration'''

    def __init__(self,
                 name,
                 subscribe_prefix='',
                 subscribe_addr='',
                 subscribe_suffix='',
                 publish_prefix='',
                 publish_suffix='',
                 schema='key-text'):
        self.name = name
        self.schema = schema
        self.subscribe_prefix = subscribe_prefix
        self.subscribe_addr = subscribe_addr
        self.subscribe_suffix = subscribe_suffix

        self.publish_prefix = publish_prefix
        self.publish_suffix = publish_suffix


class Sensor():
    '''class to store id and addr of sensor / node'''

    def __init__(self,
                 value=None,
                 node_id='',
                 sensor_id='',
                 node_addr='',
                 key='',
                 schema='key-text',
                 mode=''):
        self.node_id = node_id
        self.sensor_id = sensor_id
        self.node_addr = node_addr
        self.key = key
        self.mode = mode
        self.value = value
        self.schema = schema

    #test if any value is missing for map create
    def incomplete(self):
        return (self.node_id == '' or self.sensor_id == ''
                or self.node_addr == '' or self.key == '')


class SensorMap():
    '''container to store cofiguration data:
       maps for converting MQTT topic <--> switchboard ids,
       configured gateways,
       subscribed topics (actuator data)
    '''

    def __init__(self):
        self.gateways = {}
        self.map_topic2sensor = {}
        self.map_topic2node = {}
        self.map_sensor2topic = {}
        self.mqtt_subscibe_prefixes = []
        self.sio_rooms = []

    def __add_gw(self, gw):
        self.gateways[gw.name] = gw

    def add_gateways(self, config_dict):
        self.gateways = {}

        for gw_name, gw_config_dict in config_dict.items():
            gw = Gateway(gw_name, **gw_config_dict)
            self.__add_gw(gw)

    def join_gateways(self, sio_client):
        '''each gatewaw have its own Socket.IO room'''
        self.sensor_addr_map = {}
        self.sensor_id_map = {}

        for gw in self.gateways:
            logging.info('Socket.IO room join: {}'.format(gw))
            sio_client.emit("join", {'room': gw})

    def subscribe_gateways(self, mqtt_client):
        for gw_name, gw in self.gateways.items():

            if gw.subscribe_suffix == '':
                topic = '{}/{}'.format(gw.subscribe_prefix, gw.subscribe_addr)
            else:
                topic = '{}/{}/{}'.format(gw.subscribe_prefix, gw.subscribe_addr,
                                      gw.subscribe_suffix)

            if (gw.schema == 'key-text'):
                topic += '/+'

            logging.info('MQTT subscribe {}: {}'.format(gw_name, topic))
            mqtt_client.subscribe(topic)

    def setup_sensors(self, gw_name, config_list):
        for data in config_list:
            gw = self.gateways[gw_name]

            s = Sensor(**data, schema=gw.schema)
            if s.incomplete():
                logging.debug("skip {}".format(data))
                continue

            if gw.subscribe_prefix:
                topic_recv = "{}/{}".format(gw.subscribe_prefix, s.node_addr)
                if gw.subscribe_suffix:
                    topic_recv += "/{}".format(gw.subscribe_suffix)

                if gw.schema == 'key-text':
                    topic_recv += "/{}".format(s.key)
                    self.map_topic2sensor[topic_recv] = s
                    logging.debug("topic {} --> sensor {}.{}".format(
                        topic_recv, s.node_id, s.sensor_id))

                elif gw.schema == 'json':
                    if not topic_recv in self.map_topic2node:
                        self.map_topic2node[topic_recv] = {}
                    self.map_topic2node[topic_recv][s.key] = s
                    logging.debug(
                        "topic {} + json key {} --> sensor {}.{}".format(
                            topic_recv, s.key, s.node_id, s.sensor_id))

            if gw.publish_prefix and s.mode == 2:
                topic_send = "{}/{}".format(gw.publish_prefix, s.node_addr)
                if gw.publish_suffix:
                    topic_send += "/{}".format(gw.publish_suffix)

                topic_send += "/{}".format(s.key)

                if not s.node_id in self.map_sensor2topic:
                    self.map_sensor2topic[s.node_id] = {}

                self.map_sensor2topic[s.node_id][s.sensor_id] = topic_send
                logging.debug("known actuator {}.{} --> {}".format(
                    s.node_id, s.sensor_id, topic_send))
        return 0

    def get_sensors(self, msg):
        #if schema is key-value:
        if msg.topic in self.map_topic2sensor:
            s = self.map_topic2sensor[msg.topic]
            s.value = msg.payload.decode("ascii")
            yield s

        #json
        elif msg.topic in self.map_topic2node:
            values = json.loads(msg.payload)

            for key, s in self.map_topic2node[msg.topic].items():
                if key in values:
                    s.value = values[key]
                    yield s

        else:
            logging.debug('UNKNOWN sensor')
            range(0)  #yield nothing
