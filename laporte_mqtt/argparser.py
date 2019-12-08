# -*- coding: utf-8 -*-
'''cmd line argument parser for laporte_mqtt'''

import logging
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

    parser = ArgumentParser(description='MQTT connector for laporte')
    parser.add_argument('-H',
                        '--laporte-host',
                        action='store',
                        dest='sio_addr',
                        help='laporte socket.io host address',
                        type=str,
                        default="127.0.0.1")
    parser.add_argument('-P',
                        '--laporte-port',
                        action='store',
                        dest='sio_port',
                        help='laporte socket.io port',
                        type=int,
                        default=9128)
    parser.add_argument('-q',
                        '--mqtt-broker-host',
                        action='store',
                        dest='mqtt_addr',
                        help='mqtt broker host address',
                        type=str,
                        default="127.0.0.1")
    parser.add_argument('-r',
                        '--mqtt-broker-port',
                        action='store',
                        dest='mqtt_port',
                        help='mqtt broker port',
                        type=int,
                        default=1883)
    parser.add_argument('-k',
                        '--mqtt-keepalive',
                        action='store',
                        dest='mqtt_keepalive',
                        help='mqtt keepalive seconds',
                        type=int,
                        default=30)
    parser.add_argument('-c',
                        '--gateways-config',
                        action='store',
                        dest='gw_fname',
                        help='yaml file with mqtt config of gateways',
                        type=str,
                        default='conf/gateways.yml')
    parser.add_argument('-p',
                        '--exporter-port',
                        action='store',
                        dest='port',
                        help='prometheus metrics expose port',
                        type=int,
                        default=9129)

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
