#!/bin/sh
echo "Auto deployment for sensor program"
echo "=======================install system software======================="
# sudo apt-get update
sudo apt-get install -y mosquitto mosquitto-clients python-mosquitto vim lrzsz

echo "=======================install python packages======================="
sudo pip install apscheduler pyserial paho-mqtt

echo "============================deploy scripts============================"
echo "set config.json"
# change id in `config.json`
sensorid=$1
while [ -z $sensorid ]
do
        echo 'Please into an id for the sensor:'
        read sensorid
        echo $sensorid
done
cp config.json.default script/config.json
sed -i "s/\"sensor_id\": \"000001\"/\"sensor_id\": \"${sensorid}\"/g" script/config.json

echo "deploy script"
chmod +x script/com_lookup.sh
chmod +x script/sensor_unblock.py

sudo rm -rf /home/pi/script
cp -r ./script /home/pi/script

echo "=========================set up auto startup========================="
sudo cp sensor /etc/init.d/sensor
sudo chmod +x /etc/init.d/sensor
sudo update-rc.d sensor defaults

echo "Finished"

