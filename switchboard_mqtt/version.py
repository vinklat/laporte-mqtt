# -*- coding: utf-8 -*-
'''switchboard_mqtt app version and resources info'''

from platform import python_version
import pkg_resources

__version__ = '0.2.0rc0'


def get_build_info():
    '''get app version and resources info'''
    ret = {
        'switchboard-mqtt':
        __version__,
        'python':
        python_version(),
        'python-socketio':
        pkg_resources.get_distribution("python-socketio").version,
        'python-engineio':
        pkg_resources.get_distribution("python-engineio").version,
        'paho-mqtt':
        pkg_resources.get_distribution("paho-mqtt").version
    }
    return ret
