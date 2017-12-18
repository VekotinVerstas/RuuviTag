import sys
import datetime
import time
import json
import configparser
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



def get_iclient(host, port, db):
    # using Http
    iclient = InfluxDBClient(host=host, port=port, database=db)
    return iclient


def send_data2influxdb(d, simulate=False):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    json_data = []
    for tag in d:
        tag_data = d[tag]
        meas = 'ruuvi-{}'.format(tag)
        json_body = {
            "measurement": meas,
            "tags": {
                "dev-id": tag,
                "sensor": 'ruuvi',
            },
            "time": ts,
            "fields": {}
        }
        json_body['fields'] = tag_data
        json_data.append(json_body)
    # print(json_data)
    if simulate is False and json_data:
        iclient.write_points(json_data)
    return



# List of macs of sensors which data will be collected
# If list is empty, data will be collected for all found sensors
macs = []
# get_data_for_sensors will look data for the duration of timeout_in_sec
timeout_in_sec = 2

import os

def main(simulate=False):

    while True:
        if simulate:
            time.sleep(timeout_in_sec)
            datas = EXAMPLE_DATA
        else:
            datas = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)
        send_data2influxdb(datas, simulate=simulate)
        # print(json.dumps(datas, indent=1))
        continue


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 's':
        simulate = True
        iclient = None
    else:
        config = configparser.ConfigParser()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config.read(os.path.join(dir_path, 'config.ini'))
        timeout_in_sec = float(config['DEFAULT']['timeout'])
        # print(config.sections())
        simulate = False
        iclient = get_iclient(config['influxdb']['host'], int(config['influxdb']['port']), config['influxdb']['db'])
    main(simulate=simulate)