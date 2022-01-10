# -*- coding: utf-8 -*-
'''cmd line argument and ENV parser'''

import logging
import os
from argparse import ArgumentParser, ArgumentTypeError
from laporte_mqtt.version import __version__, app_name, get_runtime_info

# default parameters
LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
LOG_LEVEL_DEFAULT = 'INFO'
LOG_VERBOSE_DEFAULT = False
LAPORTE_HOST_DEFAULT = '127.0.0.1'
LAPORTE_PORT_DEFAULT = 1883
MQTT_BROKER_HOST_DEFAULT = '127.0.0.1'
MQTT_BROKER_PORT_DEFAULT = 1883
MQTT_KEEPALIVE_DEFAULT = 30
CONFIG_FILE_DEFAULT = 'conf/gateways.yml'
LISTEN_ADDR_DEFAULT = '0.0.0.0'
LISTEN_PORT_DEFAULT = 9129


def log_level_string_to_int(arg_string: str) -> int:
    '''get log level int from string'''

    log_level_string = arg_string.upper()
    if log_level_string not in LOG_LEVEL_STRINGS:
        message = (f"invalid choice: {log_level_string} "
                   f"(choose from {LOG_LEVEL_STRINGS})")
        raise ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the log_level_choices have not changed from our expected values
    assert isinstance(log_level_int, int)

    return log_level_int


def get_pars():
    '''
    get parameters from from command line arguments
    defaults overriden by ENVs
    '''

    env_vars = {
        'LAPORTE_HOST': {
            'default': LAPORTE_HOST_DEFAULT
        },
        'LAPORTE_PORT': {
            'default': LAPORTE_PORT_DEFAULT
        },
        'MQTT_BROKER_HOST': {
            'default': MQTT_BROKER_HOST_DEFAULT
        },
        'MQTT_BROKER_PORT': {
            'default': MQTT_BROKER_PORT_DEFAULT
        },
        'MQTT_KEEPALIVE': {
            'default': MQTT_KEEPALIVE_DEFAULT
        },
        'CONFIG_FILE': {
            'default': CONFIG_FILE_DEFAULT
        },
        'LISTEN_ADDR': {
            'default': LISTEN_ADDR_DEFAULT
        },
        'LISTEN_PORT': {
            'default': LISTEN_PORT_DEFAULT
        },
        'LOG_LEVEL': {
            'default': LOG_LEVEL_DEFAULT
        },
        'LOG_VERBOSE': {
            'default': LOG_VERBOSE_DEFAULT
        },
    }

    # defaults overriden from ENVs
    for env_var, env_pars in env_vars.items():
        if env_var in os.environ:
            default = os.environ[env_var]
            if 'default' in env_pars:
                if isinstance(env_pars['default'], bool):
                    default = bool(os.environ[env_var])
                elif isinstance(env_pars['default'], int):
                    default = int(os.environ[env_var])
            env_pars['default'] = default
            env_pars['required'] = False

    parser = ArgumentParser(description=f'{app_name.capitalize()} {__version__}')

    parser.add_argument('-H',
                        '--laporte-host',
                        action='store',
                        dest='laporte_host',
                        help=('laporte socket.io host address '
                              f'(default {LAPORTE_HOST_DEFAULT})'),
                        type=str,
                        **env_vars['LAPORTE_HOST'])
    parser.add_argument('-P',
                        '--laporte-port',
                        action='store',
                        dest='laporte_port',
                        help=('laporte socket.io host port '
                              f'(default {LAPORTE_PORT_DEFAULT})'),
                        type=int,
                        **env_vars['LAPORTE_PORT'])
    parser.add_argument('-q',
                        '--mqtt-broker-host',
                        action='store',
                        dest='mqtt_broker_host',
                        help=('MQTT broker host '
                              f'(default {MQTT_BROKER_HOST_DEFAULT})'),
                        type=str,
                        **env_vars['MQTT_BROKER_HOST'])
    parser.add_argument('-r',
                        '--mqtt-broker-port',
                        action='store',
                        dest='mqtt_broker_port',
                        help=('MQTT broker port '
                              f'(default {MQTT_BROKER_PORT_DEFAULT})'),
                        type=int,
                        **env_vars['MQTT_BROKER_PORT'])
    parser.add_argument('-k',
                        '--mqtt-keepalive',
                        action='store',
                        dest='mqtt_keepalive',
                        help=('MQTT keepalive timeout in seconds '
                              f'(default {MQTT_KEEPALIVE_DEFAULT})'),
                        type=int,
                        **env_vars['MQTT_KEEPALIVE'])
    parser.add_argument('-c',
                        '--gateways-config-file',
                        action='store',
                        dest='config_file',
                        help=("yaml  file with "
                              f"gateways configuration (default {CONFIG_FILE_DEFAULT})"),
                        type=str,
                        **env_vars['CONFIG_FILE'])
    parser.add_argument('-a',
                        '--exporter-listen-address',
                        action='store',
                        dest='listen_addr',
                        help=('prometheus metrics listen address '
                              f'(default {LISTEN_ADDR_DEFAULT})'),
                        type=str,
                        **env_vars['LISTEN_ADDR'])
    parser.add_argument('-p',
                        '--exporter-listen-port',
                        action='store',
                        dest='listen_port',
                        help=('prometheus metrics expose port '
                              f'(default {LISTEN_PORT_DEFAULT})'),
                        type=int,
                        **env_vars['LISTEN_PORT'])
    parser.add_argument('-V',
                        '--version',
                        action='version',
                        version=str(get_runtime_info()))
    parser.add_argument('-l',
                        '--log-level',
                        action='store',
                        dest='log_level',
                        help=("set the logging output level. "
                              f"{LOG_LEVEL_STRINGS} "
                              f"(default {LOG_LEVEL_DEFAULT})"),
                        type=log_level_string_to_int,
                        **env_vars['LOG_LEVEL'])
    parser.add_argument('-v',
                        '--log-verbose',
                        action='store_true',
                        dest='log_verbose',
                        help='most verbose debug level '
                        '(console only; useful for a bug hunt :)',
                        **env_vars['LOG_VERBOSE'])

    return parser.parse_args()


# get parameters from command line arguments
pars = get_pars()
