# RuuviTag experiments

This repository contains various RuuviTag experiments.

(Instructions below may be incomplete.)

# Hardware

BLE enabled Linux computer, i.e. Raspberry Pi 3 or Raspberry Pi Zero W.

# Operating system

Newest Raspbian Stretch.

# Installation
```
sudo apt install bluez bluez-hcidump
mkvirtualenv -p /usr/bin/python3 ruuvi
pip install ruuvitag_sensor
```

# Test online Ruuvitags nearby

`/home/pi/.virtualenvs/ruuvi/bin/python /home/pi/.virtualenvs/ruuvi/lib/python3.5/site-packages/ruuvitag_sensor -f`

# Configuration

Copy `config.ini-example` to `config.ini` and check all settings.
You need to run `mqtt2influx.py` in the remote server or this:
https://github.com/aapris/IoT-Web-Experiments

# Supervisor

After installing supervisord Copy `RuuviTag.conf` to `/etc/supervisor/conf.d/RuuviTag.conf`
and run:

```
sudo supervisorctl reread
sudo supervisorctl update
```
