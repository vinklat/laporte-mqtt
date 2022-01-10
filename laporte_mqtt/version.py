# -*- coding: utf-8 -*-
'''
app version and resources info
'''

import time
from platform import python_version
import pkg_resources

__version__ = '0.3.0'
app_name = 'laporte-mqtt'
# pylint: disable=consider-using-f-string
inst_id = '{0:010x}'.format(int(time.time() * 256))[:10]
app_instance = f'{app_name}_{inst_id}'


def get_version_info():
    '''get app version info'''

    ret = {
        'version': __version__,
    }

    return ret


def get_runtime_info():
    '''get app and resources runtime info'''

    modules = {
        'paho-mqtt': pkg_resources.get_distribution("paho-mqtt").version,
        'python-socketio': pkg_resources.get_distribution("python-socketio").version,
        'python-engineio': pkg_resources.get_distribution("python-engineio").version,
        'prometheus-client': pkg_resources.get_distribution("prometheus-client").version,
    }

    runtime = {
        'python_version': python_version(),
    }

    ret = {**get_version_info(), **runtime, 'python_modules': modules}

    return ret
