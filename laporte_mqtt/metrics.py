# -*- coding: utf-8 -*-
'''
Prometheus metrics to monitor requests.
'''

from prometheus_client import Summary, Counter

mqtt_message_time = Summary('mqtt_message_duration_seconds',
                            'Time spent processing MQTT message', [])

mqtt_emits_total = Counter('mqtt_emits_total', 'Total count of MQTT emits', [])

mqtt_connects_total = Counter('mqtt_client_connects_total',
                              'Total count of connects/reconnects', [])
