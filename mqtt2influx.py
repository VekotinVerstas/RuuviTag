import numbers
import datetime
import json
import sys
import os
import requests
import configparser
import argparse
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient


def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return izip(*[iter(iterable)]*n)


def get_iclient(host, port, db):
    # using Http
    iclient = InfluxDBClient(host=host, port=port, database=db)
    return iclient


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if args.quiet is False:
        print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)


def handle_message(d):
    if 'chipid' in d:
        handle_tulevaisuudenesine(d)
    elif 'tags' in d[0] and d[0]['measurement'].startswith('ruuvi'):
        # TODO: It would be wise to check organization part from MQTT topic
        handle_ruuvitag(d)
    else:
        print("No handle :(")


"""
# Tulevaisuuden esine messages look like this
{'chipid': 265091, 'sensor': 'lux', 'millis': 384502120, 'data': ['luxi', 0, '_', 0, '_', 0]}
{'chipid': 2057786, 'sensor': 'humitemp', 'millis': 383410938, 'data': ['humi', 19.48218, 'temp', 22.3805, '_', 0]}
{'chipid': 3967643, 'sensor': 'rgbgest', 'millis': 384504758, 'data': ['r', 0, 'g', 0, 'b', 0]}
{'chipid': 2056817, 'sensor': 'co2', 'millis': 370814123, 'data': ['co2_', 402, 'temp', 19, '_', 0]}
"""


def handle_tulevaisuudenesine(d):
    meas = '{}'.format(d['sensor'])
    json_body = [
        {
            "measurement": meas,
            "tags": {
                "dev-id": d['chipid']
            },
            "time": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "fields": {}
        }
    ]
    json_body[0]['fields'] = {'{}'.format(d['data'][0]): d['data'][1]}
    it = iter(d['data'])
    for x, y in zip(it, it):
        if x != '_':
            json_body[0]['fields'][x] = y
    if args.verbose > 1:
        print(json.dumps(json_body, indent=2))
    if args.dry_run is False:
        iclient.write_points(json_body)


"""
The message should look like this:

[
  {
    "tags": {
      "dev-id": "E4:F4:86:52:C5:84"
    },
    "fields": {
      "acceleration_y": -464,
      "acceleration": 1023.5311426624986,
      "acceleration_z": 24,
      "acceleration_x": 912,
      "pressure": 1021.01,
      "humidity": 38.5,
      "temperature": 20.51,
      "battery": 2941
    },
    "time": "2017-12-20T15:10:35.654711Z",
    "measurement": "ruuvi-E4:F4:86:52:C5:84"
  },
  {
    "tags": {
      "dev-id": "F8:C6:12:37:F4:3D"
    },
    "fields": {
      "acceleration_y": -624,
      "acceleration": 1025.8264960508673,
      "acceleration_z": 60,
      "acceleration_x": 812,
      "pressure": 1021.42,
      "humidity": 39.0,
      "temperature": 20.38,
      "battery": 2905
    },
    "time": "2017-12-20T15:10:35.654711Z",
    "measurement": "ruuvi-F8:C6:12:37:F4:3D"
  }
]
"""


def handle_ruuvitag(d):
    json_body = d
    # print(json_body)
    if args.verbose > 1:
        print(json.dumps(json_body, indent=2))
    if args.dry_run is False:
        iclient.write_points(json_body)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    try:
        d = json.loads(payload)
        if args.verbose > 0:
            print(payload)
    except json.decoder.JSONDecodeError as e:
        print('ERROR "{}" IN DATA: {}'.format(str(e), payload))
        return
    if isinstance(d, numbers.Number):
        print('Got number?!? {}'.format(d))
        return
    # print(d)
    handle_message(d)


parser = argparse.ArgumentParser()
parser.add_argument('-q', '--quiet', action='store_true', help='Never print a char (except on crash)')
parser.add_argument('-v', '--verbose', action='count', default=0, help='Print some informative messages')
parser.add_argument('-d', '--dry-run', action='store_true', help='Do not really save data into InfluxDB')
args = parser.parse_args()

if args.dry_run is True and args.quiet is False:
    print("Dry-run, won't really store any data")

config = configparser.ConfigParser()
dir_path = os.path.dirname(os.path.realpath(__file__))
config.read(os.path.join(dir_path, 'config.ini'))
MQTT_TOPIC = config['mqtt2influx']['topic']

client = mqtt.Client()
client.username_pw_set(config['mqtt2influx']['username'], config['mqtt2influx']['password'])
client.on_connect = on_connect
client.on_message = on_message
client.connect(config['mqtt2influx']['host'], int(config['mqtt2influx']['port']), 60)
iclient = get_iclient(config['influxdb']['host'], int(config['influxdb']['port']),
                      config['influxdb']['db'])


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
