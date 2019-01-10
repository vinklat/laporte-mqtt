FROM python:3-alpine

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /switchboard-mqtt
COPY conf/*yml /switchboard-mqtt/conf/
COPY *.py /switchboard-mqtt/

ENTRYPOINT [ "python", "./switchboard-mqtt.py" ]

