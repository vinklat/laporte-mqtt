# -*- coding: utf-8 -*-
'''laporte_mqtt app version and resources info'''

from platform import python_version
import pkg_resources

__version__ = '0.2.2'


def get_build_info():
    '''get app version and resources info'''
    ret = {
        'laporte-mqtt': __version__,
        'python': python_version(),
        'python-socketio': pkg_resources.get_distribution("python-socketio").version,
        'python-engineio': pkg_resources.get_distribution("python-engineio").version,
        'paho-mqtt': pkg_resources.get_distribution("paho-mqtt").version
    }
    return ret
