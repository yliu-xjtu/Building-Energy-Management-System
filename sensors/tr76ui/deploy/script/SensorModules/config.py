#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 16:40:14 2017

config file module

@author: yliu
"""

#coding=utf8
 
import json
import os
import sys

# function: load default config
def load_cfg_default():
    out_format='csv' # null, detailed, csv
    
    # main config
    cfg_default={}
    cfg_default['version']='1.0'
    cfg_default['debug']=0
    cfg_default['out_format']=out_format
    
    # sensor parameters
    cfg_default['sensor_id'] = "000001"

    
    # serial port parameters
    cfg_default['COM']={}
    cfg_default['COM']['COMNAME']='/dev/ttyUSB0'
    cfg_default['COM']['BUADRATE']=19200
    
    # mqtt paramters
    HOST = "192.168.100.12"
    qos=0
    mqtt_username='pkl'
    mqtt_password='pkems'
    cfg_default['mqtt']={}
    cfg_default['mqtt']['host']=HOST
    cfg_default['mqtt']['qos']=qos
    cfg_default['mqtt']['username']=mqtt_username
    cfg_default['mqtt']['password']=mqtt_password

    return cfg_default

# function: load config file
def load_cfg(cfg_filename):
    cfg_path_filename=os.path.join(sys.path[0],cfg_filename)
    if not os.path.isfile(cfg_path_filename):
        print "config.json not found in current directory"
        print "create and use default config"
        cfg=load_cfg_default()
        save_cfg(cfg,cfg_path_filename)
    else:
        print "config.json found in current directory"
        print "load config.json"
        with open(cfg_path_filename,'rb') as cfgfile:
            cfg=json.load(cfgfile)
    return cfg

# function: save config file
def save_cfg(cfg,cfg_filename):
    with open(cfg_filename,'wb') as cfgfile:
        json.dump(cfg,cfgfile,indent=2)
        return True
    return False
        
if __name__ == "__main__":
    cfg=load_cfg('config.json')     
    cfg['COM']['COMNAME']='COM4'
    save_cfg(cfg,'config.json')
