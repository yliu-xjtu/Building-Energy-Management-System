#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Recoder sensor module

@author: yliu
"""

import time
# import serial
import array
import json
import socket
from time import sleep


cmd_begin = [0x00,0x00,0x00,0x00] # trick
#cmd_read_meas = msg.payload
cmd_read_meas = [0x01,0x33, 0x00, 0x00, 0x00, 0x34, 0x00]

# convert command to byte stream
send_begin_cmd =array.array('B',cmd_begin).tostring()
send_cmd = array.array('B',cmd_read_meas).tostring()

# function: print elements in list in hex format
def print_hex(data):
    for element in data:
        print "0x%02x"%element,
    print ""

# function: read measurements from sensor through serial port communication
# params:
# ser: serial port handler
# debug: flag
#    0(default): no debug info
#    1: has debug info
def read_meas(ser,debug=0):
    # send begin command
    ser.write(send_begin_cmd)
    sleep(0.1)
    # send data
    ser.write(send_cmd)

    # debug
    #ser.write(array.array('B',[0x00,0x00,0x00]).tostring())
    #ser.write(array.array('B',[0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x33,0x00,0x00,0x00,0x34,0x00]).tostring())

    # wait for some time to ensure receiving all data in recv buffer
    sleep(1)
    # number of bytes in recv buffer
    n=ser.inWaiting()
    if n>0:
        recv_data = ser.read(n)
    else:
        recv_data = ''
    # type: string to list
    data = map(ord,recv_data)

    # debug info: sent & received data
    if debug>=1:
        print "sent data:" + str(len(send_cmd))
        print_hex(cmd_read_meas)
        
        print "received data:" + str(n)
        print_hex(data)    
    return data


# function: generate description from measurements
def gen_desc(measurements):
    if measurements is None:
        print 'warning: no measurements found'
        return None
    
    meas_ts = measurements[0]
    meas_co2 = measurements[1]
    meas_temp = measurements[2]
    meas_hum = measurements[3]

    desc_detailed = ""  # detailed description
    desc_csv = ""  # comma seperated description for csv output

    desc_detailed = desc_detailed + "Timestamp: " + meas_ts + ", "
    desc_detailed = desc_detailed + "CO2: " + str(meas_co2) + "ppm, "
    desc_detailed = desc_detailed + "Temperature: " + str(meas_temp) + "degC, "
    desc_detailed = desc_detailed + "Humidity: " + str(meas_hum) + "%"
    desc_csv = meas_ts + ", " + str(meas_co2) + ", " + str(meas_temp) + ", " + str(meas_hum)

    return (desc_detailed, desc_csv)



# convert measurements into json format
def json_meas(meas_ts,meas_co2,meas_temp,meas_hum):
    meas={}
    # meas_ts=time.strftime("%Y-%m-%d %H:%M:%S", sampling_time)
    meas['timestamp'] = meas_ts
    meas['co2'] = meas_co2
    meas['temp'] = meas_temp
    meas['hum'] = meas_hum
    return meas

def json_payload(sensor_id,meas):
    payload_meas = {}
    payload_meas['id']=sensor_id
    payload_meas['meas']=meas
    payload_meas_str=json.dumps(payload_meas)
    return payload_meas_str

# function: parse measurment data
def parse_meas(data):
    global str_flag
    # Command Sucessful
    if (data[0] == 0x01 and data[1] == 0x33 and data[2] == 0x06):
        data_len = data[3] + (data[4] << 8)
        # Checksum validation
        chk_sum_data = sum(data[0:5 + data_len])
        chk_sum = data[5 + data_len] + ((data[6 + data_len]) << 8)
        if (chk_sum_data == chk_sum):
            data_co2 = data[5] + (data[5 + 1] << 8)
            data_temp = data[5 + 2] + (data[5 + 3] << 8)
            data_hum = data[5 + 4] + (data[5 + 5] << 8)

            # parse co2
            if ((data_co2 & 0xfff0) == 0xf000):  # error code
                meas_co2 = None
                err_co2 = data_co2
            else:
                S = (data_co2 >> 15)
                E = (data_co2 >> 12) & 0x07
                M = data_co2 & 0xfff
                # N= (S<<13)|M # N is signed 13-bit integer
                if S == 0:
                    N = M
                else:
                    N = 2**13 - M
                meas_co2 = N * (2**E)

            # parse temperature
            meas_temp = (data_temp - 1000.0) / 10

            # parse humidity
            meas_hum = (data_hum - 1000.0) / 10

            sampling_time = time.localtime()
            meas_ts = time.strftime("%Y-%m-%d %H:%M:%S", sampling_time)
            
            return (meas_ts, meas_co2, meas_temp, meas_hum)
        else:
            # return None if error
            return None

# return example of measurement readings
def example_meas():
    sampling_time=time.localtime(time.time())
    meas_ts = time.strftime("%Y-%m-%d %H:%M:%S", sampling_time)
    meas_co2 = 670
    meas_temp = 16.70
    meas_hum = 10
    return (meas_ts,meas_co2,meas_temp,meas_hum)

# function: get mac address
# http://www.cnblogs.com/Jerryshome/archive/2011/11/30/2269365.html			
def get_mac_addr():
    import uuid
    node = uuid.getnode()
    mac = uuid.UUID(int = node).hex[-12:]
    return mac

# function (deprecated): get ip address
# http://blog.csdn.net/heizistudio/article/details/38413739
# get wrong result on raspberrry pi    
def get_ip_addr():

    #get host name
    myname = socket.getfqdn(socket.gethostname())
    #get ip addr
    myaddr = socket.gethostbyname(myname)
    return myaddr

# function: get ip address
# works well on raspberry pi
# https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
			
if __name__ == "__main__":
	# received data for testing
	data=[0x01, 0x33, 0x06, 0x08, 0x00, 0xe1, 0x01, 0xc8, 0x04, 0x74, 0x04, 0x00, 0x00, 0x68, 0x02]
	print "data to be parsed:"
	print_hex(data)
	print "parsing data....."
	# decoding measurement
	measurements = parse_meas(data)
	
	# generate description
	descs = gen_desc(measurements)
	# print detailed description
	print "detailed description:"
	print descs[0]
	# print csv description
	print "csv description:"
	print descs[1]
	
	
	
	
	
	
