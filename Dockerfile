FROM python:3-alpine

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /tmp/x
COPY switchboard_mqtt/*py ./switchboard_mqtt/
COPY setup.py README.md MANIFEST.in LICENSE requirements.txt ./
RUN  pip install . 

WORKDIR /switchboard-mqtt
COPY conf/*yml ./conf/

ENTRYPOINT [ "switchboard-mqtt" ]
