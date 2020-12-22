# -*- coding: utf-8 -*-
'''cmd line argument parser for laporte_mqtt'''

import logging
import os
from argparse import ArgumentParser, ArgumentTypeError
from laporte_mqtt.version import __version__, get_build_info

_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


def log_level_string_to_int(arg_string):
    '''get log level int from string'''

    log_level_string = arg_string.upper()
    if log_level_string not in _LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(
            log_level_string, _LOG_LEVEL_STRINGS)
        raise ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the log_level_choices have not changed from our expected values
    assert isinstance(log_level_int, int)

    return log_level_int


def get_pars():
    '''get parameters from from command line arguments'''

    env_vars = {
        'LAPORTE_HOST': {
            'default': '127.0.0.1'
        },
        'LAPORTE_PORT': {
            'default': 9128
        },
        'MQTT_BROKER_HOST': {
            'default': '127.0.0.1'
        },
        'MQTT_BROKER_PORT': {
            'default': 1883
        },
        'MQTT_KEEPALIVE': {
            'default': 30
        },
        'CONFIG_FILE': {
            'default': 'conf/gateways.yml'
        },
        'LISTEN_ADDR': {
            'default': '0.0.0.0'
        },
        'LISTEN_PORT': {
            'default': 9129
        },
        'LOG_LEVEL': {
            'default': 'DEBUG'
        },
    }

    for env_var, env_pars in env_vars.items():
        if env_var in os.environ:
            if isinstance(env_pars['default'], bool):
                env_vars[env_var]['default'] = bool(os.environ[env_var])
            elif isinstance(env_vars[env_var]['default'], int):
                env_vars[env_var]['default'] = int(os.environ[env_var])
            else:
                env_vars[env_var]['default'] = os.environ[env_var]
            env_vars[env_var]['required'] = False

    parser = ArgumentParser(description='MQTT connector for laporte')
    parser.add_argument('-H',
                        '--laporte-host',
                        action='store',
                        dest='laporte_host',
                        help='laporte socket.io host address (default {0})'.format(
                            env_vars['LAPORTE_HOST']['default']),
                        type=str,
                        **env_vars['LAPORTE_HOST'])
    parser.add_argument('-P',
                        '--laporte-port',
                        action='store',
                        dest='laporte_port',
                        help='laporte socket.io port (default {0})'.format(
                            env_vars['LAPORTE_PORT']['default']),
                        type=int,
                        **env_vars['LAPORTE_PORT'])
    parser.add_argument('-q',
                        '--mqtt-broker-host',
                        action='store',
                        dest='mqtt_broker_host',
                        help='mqtt broker host address (default {0})'.format(
                            env_vars['MQTT_BROKER_HOST']['default']),
                        type=str,
                        **env_vars['MQTT_BROKER_HOST'])
    parser.add_argument('-r',
                        '--mqtt-broker-port',
                        action='store',
                        dest='mqtt_broker_port',
                        help='mqtt broker port (default {0})'.format(
                            env_vars['MQTT_BROKER_PORT']['default']),
                        type=int,
                        **env_vars['MQTT_BROKER_PORT'])
    parser.add_argument('-k',
                        '--mqtt-keepalive',
                        action='store',
                        dest='mqtt_keepalive',
                        help='mqtt keepalive seconds (default {0})'.format(
                            env_vars['MQTT_KEEPALIVE']['default']),
                        type=int,
                        **env_vars['MQTT_KEEPALIVE'])
    parser.add_argument('-c',
                        '--gateways-config-file',
                        action='store',
                        dest='config_file',
                        help='yaml file with mqtt config of gateways'
                        ' (default {0})'.format(env_vars['CONFIG_FILE']['default']),
                        type=str,
                        **env_vars['CONFIG_FILE'])
    parser.add_argument('-a',
                        '--exporter-listen-address',
                        action='store',
                        dest='listen_addr',
                        help='prometheus metrics listen address (default {0})'.format(
                            env_vars['LISTEN_ADDR']['default']),
                        type=str,
                        **env_vars['LISTEN_ADDR'])
    parser.add_argument('-p',
                        '--exporter-listen-port',
                        action='store',
                        dest='listen_port',
                        help='prometheus metrics expose port (default {0})'.format(
                            env_vars['LISTEN_PORT']['default']),
                        type=int,
                        **env_vars['LISTEN_PORT'])

    parser.add_argument('-V',
                        '--version',
                        action='version',
                        version=str(get_build_info()))

    parser.add_argument(
        '-l',
        '--log-level',
        action='store',
        dest='log_level',
        help='set the logging output level. {0}'.format(_LOG_LEVEL_STRINGS),
        type=log_level_string_to_int,
        default='INFO')

    return parser.parse_args()
