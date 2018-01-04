import sys
import os
import datetime
import time
import json
import configparser
import argparse
import paho.mqtt.client as mqtt

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from influxdb import InfluxDBClient


EXAMPLE_DATA = {
 "F8:C6:12:37:F4:3D": {
  "pressure": 996.34,
  "humidity": 40.5,
  "acceleration_x": -16,
  "temperature": 20.54,
  "acceleration_z": 1004,
  "acceleration": 1004.7726110916838,
  "battery": 2941,
  "acceleration_y": 36
 },
 "E4:F4:86:52:C5:84": {
  "pressure": 995.87,
  "humidity": 40.5,
  "acceleration_x": -24,
  "temperature": 19.85,
  "acceleration_z": 1036,
  "acceleration": 1036.4709354342745,
  "battery": 2905,
  "acceleration_y": 20
 }
}


def on_connect(client, userdata, flags, rc):
    print("Connected with result code {}".format(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#")


def get_iclient(host, port, db):
    # using Http
    iclient = InfluxDBClient(host=host, port=port, database=db)
    return iclient


def create_influxdb_packet(d):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    json_data = []
    meas = 'ruuvitag'
    for tag in d:
        tag_data = d[tag]
        json_body = {
            "measurement": meas,
            "tags": {
                "dev-id": tag,
            },
            "time": ts,
            "fields": {}
        }
        json_body['fields'] = tag_data
        json_data.append(json_body)
    return json_data


def http_post2influxdb(d, simulate=False):
    json_data = create_influxdb_packet(d)
    # print(json_data)
    if simulate is False and json_data:
        iclient.write_points(json_data)
    return


def mqtt2influxdb(d):
    json_data = create_influxdb_packet(d)
    # print(json_data)
    if simulate is False and json_data:
        iclient.write_points(json_data)
    return


# List of macs of sensors which data will be collected
# If list is empty, data will be collected for all found sensors
macs = []
# get_data_for_sensors will look data for the duration of timeout_in_sec
timeout_in_sec = 2


def main(args):
    while True:
        if args.simulate:
            time.sleep(timeout_in_sec)
            datas = EXAMPLE_DATA
        else:
            try:
                datas = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)
            except Exception as err:
                print('ERROR at {}'.format(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")))
                print('{}'.format(err))
        if args.protocol == 'http':
            http_post2influxdb(datas, simulate=args.simulate)
            if args.verbose > 1:
                print('POSTing data "{}"'.format(json.dumps(datas)))
        elif args.protocol == 'mqtt':
            json_data = create_influxdb_packet(datas)
            pl = json.dumps(json_data)
            if args.verbose > 1:
                print('Publish MQTT message {}  on topic {}'.format(pl, args.topic))
            result, mid = mclient.publish(args.topic, payload=pl, qos=0, retain=False)
            if args.quiet is False  and result != 0:
                print('MQTT publish error! {}'.format(result))
        else:
            if args.quiet is False:
                print("Not sending because protocol is not defined")
        if args.verbose > 0:
            print(json.dumps(datas, indent=1))
        continue



if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quiet', action='store_true', help='Never print a char (except on crash)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Print some informative messages')
    parser.add_argument('-p', '--protocol', choices=['mqtt', 'http'], help='Use MQTT or HTTP to send data. No data will be sent if protocol is not defined')
    parser.add_argument('-s', '--simulate', action='store_true', help='Simulate Ruuvitags, do not really scan')
    args = parser.parse_args()
    iclient = None
    mclient = None
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(dir_path, 'config.ini'))
    timeout_in_sec = float(config['DEFAULT']['timeout'])
    if args.protocol:
        if args.protocol.lower() == 'http':
            iclient = get_iclient(config['influxdb']['host'], int(config['influxdb']['port']),
                                  config['influxdb']['db'])
        if args.protocol.lower() == 'mqtt':
            mclient = mqtt.Client()
            mclient.username_pw_set(config['mqtt']['username'], config['mqtt']['password'])
            mclient.on_connect = on_connect
            # mclient.on_message = on_message
            mclient.connect(config['mqtt']['host'], int(config['mqtt']['port']), 60)
            args.topic = config['mqtt']['topic']
    try:
        main(args)
    except KeyboardInterrupt:
        mclient.disconnect()
        print("Good bye")
