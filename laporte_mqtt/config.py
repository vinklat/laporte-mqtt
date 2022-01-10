# -*- coding: utf-8 -*-
'''
Objects that collect mqtt prefixes setup for sensors
'''

# pylint: disable=too-few-public-methods
import sys
import logging
from yaml import safe_load, YAMLError

SCHEMA_JSON = 0
SCHEMA_VALUE = 1

# create logger
logging.getLogger(__name__).addHandler(logging.NullHandler())


class GatewayConfig():
    '''mqtt setup of one gateway'''
    def __init__(self,
                 name,
                 subscribe_topic='#',
                 subscribe_schema=SCHEMA_JSON,
                 subscribe_pattern='.*/(.*)',
                 publish_schema=SCHEMA_JSON,
                 publish_pattern=''):

        self.name = name
        self.subscribe_topic = subscribe_topic
        self.subscribe_schema = subscribe_schema
        self.subscribe_pattern = subscribe_pattern
        self.publish_schema = publish_schema
        self.publish_pattern = publish_pattern


class GatewaysConfig():
    '''container to store mqtt setup from config file'''
    @staticmethod
    def load_config(filename):
        '''read config file and parse yaml to config_dict'''

        ret = []

        try:
            with open(filename, 'r', encoding='utf8') as stream:
                try:
                    config_dict = safe_load(stream)
                except YAMLError as exc:
                    logging.error(exc)
                    sys.exit(1)
        except FileNotFoundError as exc:
            logging.critical(exc)
            sys.exit(1)

        for gateway_name, gateway_setup in config_dict.items():
            params = {"name": gateway_name}

            for direction in ['subscribe', 'publish']:
                if direction in gateway_setup:
                    if 'topic' in gateway_setup[direction]:
                        params[direction + "_topic"] = gateway_setup[direction]['topic']

                    if 'schema' in gateway_setup[direction]:
                        schemas_map = {"json": SCHEMA_JSON, 'value': SCHEMA_VALUE}
                        schema_str = gateway_setup[direction]['schema']
                        try:
                            schema = schemas_map[schema_str]
                        except KeyError:
                            logging.error("unknown schema %s", schema_str)

                        params[direction + '_schema'] = schema
                    if 'pattern' in gateway_setup[direction]:
                        params[direction +
                               '_pattern'] = gateway_setup[direction]['pattern']

            gw_item = GatewayConfig(**params)
            ret.append(gw_item)

        return ret

    def __init__(self, filename):
        self.gateway_list = self.load_config(filename)

    def get(self):
        '''generate gateways used in a for loop'''

        for gateway in self.gateway_list:
            yield gateway

    def get_names(self):
        '''return a list of gateway names'''

        for gateway in self.gateway_list:
            yield gateway.name

    def find_gateway(self, gateway_name):
        '''return a gateway with given name'''

        for gateway in self.gateway_list:
            if gateway.name == gateway_name:
                return gateway
        raise KeyError
