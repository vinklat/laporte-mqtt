# -*- coding: utf-8 -*-
'''
Configured logger (light version)
'''

import logging
from laporte_mqtt.argparser import pars


class ConfLogger():
    '''
    set a logger with configured handlers and filters
    '''
    def __init__(self, name, log_level=logging.DEBUG, log_verbose=False):
        '''
        set logger
        '''

        if log_verbose:
            log_level = logging.DEBUG

        handlers = [
            logging.StreamHandler(),
        ]

        logging.basicConfig(format='%(levelname)s %(module)s %(funcName)s:'
                            ' %(message)s',
                            level=log_level,
                            handlers=handlers)

        if not log_verbose:
            for module in ['socketio', 'engineio']:
                logging.getLogger(module).setLevel(logging.CRITICAL)

        self.logger = logging.getLogger(name)

    def get_logger(self):
        return self.logger


cl = ConfLogger(__name__, log_level=pars.log_level, log_verbose=pars.log_verbose)
logger = cl.get_logger()
