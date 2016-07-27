#!/usr/bin/env python
# Communication script for ADAM4017 using ADAM4561 USB to RS485 converter
# Eirik Haustveit, 2016

# Create a connection to the ADAM4017 module, and read the analog values.
# Compute the corresponding measurements based upon knowledge of the actual
# sensors that are connected, i.e. this is a very application spesific
# script.

import sys
import serial
import io
import time
import datetime

import argparse
import configparser


import paho.mqtt.client as mqtt

import logging
import logging.handlers

from adam4000 import adam4017

#Settings
CONFIG_FILENAME = '/srv/refrigerators/adamRead/adamread.conf'
LOG_FILENAME = '/tmp/adamread.log'
LOG_LEVEL = logging.INFO

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)

# create a file handler
#handler = logging.FileHandler('adamRead.log')
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)


# Class to capture stdout and sterr in the log
class serviceLogger(object):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        # Check if message is empty
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())

# Use logfile as standard output and standard error
sys.stdout = serviceLogger(logger, logging.INFO)
sys.stderr = serviceLogger(logger, logging.ERROR)



def main():
    print('Starting ADAM4017 temperature and humidity acquisition')

    now = datetime.datetime.now()
    logger.info('Program executed at: %s ' % now.isoformat())

    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILENAME)

        adam4000conf = config['ADAM4000']
        logger.info('Creating instance of ADAM4017 class.')
        sensor = adam4017(adam4000conf['serial_port'],int(adam4000conf['device_addr']))

        logger.info('Creating MQTT instance')
        mqttc = mqtt.Client()

        print('Configuration: ' + sensor.readConfiguration())	
        print('Firmware version: ' + sensor.readFirmwareVersion())	
        print('Module name: ' + sensor.readModuleName())	
        
        print('AI0: ' + str(sensor.readAnalogIn(0)))
        print('AI1: ' + str(sensor.readAnalogIn(1)))
        print('AI2: ' + str(sensor.readAnalogIn(2)))
        print('AI3: ' + str(sensor.readAnalogIn(3)))

        mqttconf = config['MQTT']
        logger.info('Connecting to MQTT')
        mqttc.connect(mqttconf['address'])
        mqttc.loop_start()

        while True:
          
            # Refrigerator A: 
            humidity = (sensor.readAnalogIn(0)-4) * 6.25
            humidity = float('{0:.1f}'.format(humidity))
            logger.info('Humid A: ' + str(humidity))
           
            temperature = -40 + (sensor.readAnalogIn(1)-4) * 7.5
            temperature = float('{0:.1f}'.format(temperature))
            
            logger.info('Temp A: ' + str(temperature))
            
            mqttc.publish("adam4017/temperatureA", temperature)
            mqttc.publish("adam4017/humidityA", humidity)
    
            # Refrigerator B: 
            humidity = (sensor.readAnalogIn(2)-4) * 6.25
            logger.info('Humid B: ' + str(humidity))
           
            temperature = -40 + (sensor.readAnalogIn(3)-4) * 7.5
    
            logger.info('Temp B: ' + str(temperature))
            
            mqttc.publish("adam4017/temperatureB", temperature)
            mqttc.publish("adam4017/humidityB", humidity)
           
            time.sleep(5)

    except KeyError:
        logger.error('Invalid configuration file')
    except:
        raise


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt')
