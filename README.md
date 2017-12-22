# RuuviTag experiments

This repository contains various RuuviTag experiments.

# Installation
```
sudo apt install bluez bluez-hcidump
mkvirtualenv -p /usr/bin/python3 ruuvi
pip install ruuvitag_sensor
```

# Test online Ruuvitags nearby
/home/pi/.virtualenvs/ruuvi/bin/python /home/pi/.virtualenvs/ruuvi/lib/python3.5/site-packages/ruuvitag_sensor -f

# Crontab
Add something like this to cron (`crontab -e`):
@reboot sleep 10 && cd /home/pi/Ruuvi && /home/pi/.virtualenvs/ruuvi/bin/python /home/pi/Ruuvi/all_tags2influx.py -q -p http
