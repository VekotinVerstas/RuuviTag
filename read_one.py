from ruuvitag_sensor.ruuvi import RuuviTagSensor
import sys

# List of macs of sensors which data will be collected
# If list is empty, data will be collected for all found sensors
macs = [sys.argv[1]]
# get_data_for_sensors will look data for the duration of timeout_in_sec
timeout_in_sec = 1

d = {}
# Dictionary will have lates data for each sensor
while True:
    datas = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)
    d2 = datas.get(sys.argv[1])
    if d2 and d != d2:
        print('{acceleration} x={acceleration_x} y={acceleration_y} z={acceleration_z}'.format(**d2))
        d = d2
