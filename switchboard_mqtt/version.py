# -*- coding: utf-8 -*-
'''switchboard_mqtt app version and resources info'''

from platform import python_version
import pkg_resources

__version__ = '0.1.0'


def get_build_info():
    '''get app version and resources info'''
    ret = {
        'switchboard-mqtt':
        __version__,
        'python':
        python_version(),
        'socketIO-client':
        pkg_resources.get_distribution("socketIO-client").version,
        'paho-mqtt':
        pkg_resources.get_distribution("paho-mqtt").version
    }
    return ret
