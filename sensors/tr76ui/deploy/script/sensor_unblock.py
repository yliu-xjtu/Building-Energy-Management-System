#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 14:58:19 2017

@author: yliu
"""

# Python定时任务的实现方式
# https://lz5z.com/Python%E5%AE%9A%E6%97%B6%E4%BB%BB%E5%8A%A1%E7%9A%84%E5%AE%9E%E7%8E%B0%E6%96%B9%E5%BC%8F/

# -*- coding: utf-8 -*-
import serial
import paho.mqtt.client as mqtt
import json
import syslog,sys,os

from time import sleep
import time
import SensorModules.RecorderSensor as rec
from SensorModules import config
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import base64
import re





# load config
cfg=config.load_cfg('config.json')

# serial port parameters
COMNAME=cfg['COM']['COMNAME']#'/dev/ttyUSB0'
BUADRATE=cfg['COM']['BUADRATE']
debug=cfg['debug']
out_format=cfg['out_format'] # null, detailed, csv

# sensor parameters
sensor_id = cfg['sensor_id']

# mqtt parameters
HOST = cfg['mqtt']['host']
qos = cfg['mqtt']['qos']
mqtt_username = cfg['mqtt']['username']
mqtt_password = cfg['mqtt']['password']
# sensor's message to DataBase
mqtt_msg_measurement_report="sensors/tr76ui/report/meas"
mqtt_msg_info_report="sensors/tr76ui/report/info"

# sensor's message to sensor management
mqtt_msg_measurement_response="sensors/tr76ui/response/meas"
mqtt_msg_info_response="sensors/tr76ui/response/info"
# query message from sensor management
mqtt_msg_measurement_query="sensors/tr76ui/query/meas"
mqtt_msg_info_query="sensors/tr76ui/query/info"

# reg pattern for topics
# http://python3-cookbook.readthedocs.io/zh_CN/latest/c02/p04_match_and_search_text.html
#pat_meas = re.compile(r'sensors/tr76ui/response/meas')

# logging format
# https://stackoverflow.com/questions/28724459/no-handlers-could-be-found-for-logger-apscheduler-executors-default
logging.basicConfig()
#log = logging.getLogger('apscheduler.executors.default')
#log.setLevel(logging.INFO)  # DEBUG
#log.setLevel(logging.ERROR)  # RELEASE
#
#fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
#h = logging.StreamHandler()
#h.setFormatter(fmt)
#log.addHandler(h)

# statistics data for query measurement
query_meas_num = 0
query_meas_err = 0


def on_connect(client, userdata, flags, rc):
    if debug==1:
        print("Connected with result code "+str(rc))
    client.subscribe(mqtt_msg_measurement_query)
    client.subscribe(mqtt_msg_info_query)

def on_publish(client, userdata, mid):
    if debug==1:
        print("a message has completed transmissed to the broker")

def on_subscribe(client,userdata,mid,granted_qos):
    if debug==1:
        print("Broker responds to a subscribe request")

def on_message(client, userdata, msg):
    if debug==1:
        print "received message topic: "+(msg.topic)

    # query device info
    if(msg.topic==mqtt_msg_info_query):
        pollingInfoSub(mqtt_msg_info_response,1)

    # query measurement
    if(msg.topic==mqtt_msg_measurement_query):
        pollingMeasSub(mqtt_msg_measurement_response,1)


def pollingMeasSub(topic,qos):
    # open serial port
    with serial.Serial(COMNAME, BUADRATE, timeout=2) as ser:
        global query_meas_num, query_meas_err
        query_meas_num += 1

        # read measurement frome sensor
        data=rec.read_meas(ser)
        # parse received data
        if len(data)!=0:
            measurements = rec.parse_meas(data)
            descs = rec.gen_desc(measurements)
            if debug==1:
                if out_format=="detailed":
                    print descs[0]
                elif out_format=="csv":
                    print descs[1]

            payload=rec.json_payload(sensor_id,measurements)
            client.publish(topic,payload,qos)
        else:
            query_meas_err += 1

        # statistics for measurement query failure
        if query_meas_num==100:
            print "Sent 100 meas query recently, and %d failed."%(query_meas_err)
            query_meas_num=0
            query_meas_err=0


def pollingInfoSub(topic,qos):
     info = {}
     info['id'] = sensor_id
     info['mac_addr'] = rec.get_mac_addr()
     info['ip_addr'] = rec.get_ip_address()
     sampling_time = time.localtime()
     meas_ts = time.strftime("%Y-%m-%d %H:%M:%S", sampling_time)
     info['Timestamp']=meas_ts 
     s = info['Timestamp']+info['id'] + info['mac_addr'] + info['ip_addr'] + "pkems"
     info['checksum'] = base64.b64encode(s)  # used for checking
     payload = json.dumps(info)
     if debug==1:
        print payload
     client.publish(topic, payload, qos)


def pollingMeas():
   #print "start meas"
    pollingMeasSub(mqtt_msg_measurement_report, 0)


def pollingInfo():
   #print "start info"
    pollingInfoSub(mqtt_msg_info_report, 0)


def resubscribe():
    client.subscribe(mqtt_msg_measurement_query)
    client.subscribe(mqtt_msg_info_query)

# default 60s
def main(inc1=10,inc2=15,inc3=30):
    scheduler = BackgroundScheduler()
    job1 = scheduler.add_job(pollingMeas, 'interval', seconds=inc1)
    job2 = scheduler.add_job(pollingInfo, 'interval', seconds=inc2)
    job3 = scheduler.add_job(resubscribe, 'interval', seconds=inc3)
    scheduler.start()



if __name__ == "__main__":

    client = mqtt.Client(protocol=3)
    client.username_pw_set(mqtt_username, mqtt_password) # 必须设置，否则会返回「Connected with result code 4」
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message
    print "start"
    # try connecting until connected
    while  True:
        try:
            print "try to connect"
            client.connect(HOST, 61613, 60)
            print "success"
            break
        except:
            print "error on socket"
            time.sleep(5)
            
    main(60,15*60,90)
    client.loop_forever()
    
    

