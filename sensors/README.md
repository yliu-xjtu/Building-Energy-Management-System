# Building-Energy-Management-System

This code is used for data collection from tr76ui sensors. And the final sensor data will be sent through a MQTT broker.

Deploy code on a raspberry Pi for data collecting from tr76ui sensors via serial ports.

After uploading the code onto raspberry pi via SFTP or ZMODEM, we can use the following commands to make the raspberry pi run the sensor data collecting scripts automatically with auto-startup.

```shell
cd deploy
chmod +x deploy.sh
./deploy.sh
```