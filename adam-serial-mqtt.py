#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
LOG_LEVEL = logging.DEBUG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
handler.setLevel(LOG_LEVEL)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


## Class to capture stdout and sterr in the log
#class serviceLogger(object):
#    def __init__(self, logger, level):
#        self.logger = logger
#        self.level = level
#
#    def write(self, message):
#        # Check if message is empty
#        if message.rstrip() != "":
#            self.logger.log(self.level, message.rstrip())
#
## Use logfile as standard output and standard error
#sys.stdout = serviceLogger(logger, logging.INFO)
#sys.stderr = serviceLogger(logger, logging.ERROR)
#


def main():
    print('Starting ADAM4017 temperature and humidity acquisition')

    now = datetime.datetime.now()
    logger.info('Program executed at: %s ' % now.isoformat())

    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILENAME)

        adam4000conf = config['ADAM4000']
        logger.info('Creating instance of ADAM4017 class.')
        sensor = adam4017(adam4000conf['serial_port'],int(adam4000conf['device_addr']),logger)

        logger.info('Creating MQTT instance')
        mqttc = mqtt.Client()

        # Set a last will message, to be displayed if the broker dectects
        # that the communication link is lost.
        mqttc.will_set('adam4017/will', 'MQTT client failure', 0, False)

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

            # The Vaisala HMT100 temperature and humiditiy sensors have the following
            # measurement ranges:
            # 0 .. 100%RH 4-20mA
            # -40 .. +80 deg C 4-20mA

            # Refrigerator A: 
            humidity = ((sensor.readAnalogIn(0)-4) * 6.25) + 1
            humidity = float('{0:.1f}'.format(humidity))
            if (humidity < 0) or (humidity > 100):
                logger.warning('Invalid humidity data: ' + str(humidity))
                mqttc.publish("adam4017/humidityA",-1)
                #mqttc.publish("adam4017/humidityA","Ugyldig luftfuktigheitsdata rom A.")
            else:
                logger.info('Humid A: ' + str(humidity))
                mqttc.publish("adam4017/humidityA", humidity)
           
            temperature = (-40 + (sensor.readAnalogIn(1)-4) * 7.5) + 1
            temperature = float('{0:.1f}'.format(temperature))
            
            #logger.info('Temp A: ' + str(temperature))
            
            #mqttc.publish("adam4017/temperatureA", temperature)

            if (temperature < 0) or (temperature > 70):
                logger.warning('Invalid temperature data: ' + str(temperature))
                mqttc.publish("adam4017/temperatureA", -1)
                #mqttc.publish("adam4017/temperatureA", "Ugyldig temperaturdata rom A.")
            else:
                logger.info('Temp A: ' + str(temperature))
                mqttc.publish("adam4017/temperatureA", temperature)
 

    
            # Refrigerator B: 
            humidity = ((sensor.readAnalogIn(2)-4) * 6.25) + 1
            humidity = float('{0:.1f}'.format(humidity))
            if (humidity < 0) or (humidity > 100):
                logger.warning('Invalid humidity data room B: ' + str(humidity))
                mqttc.publish("adam4017/humidityB",-1)
                #mqttc.publish("adam4017/humidityB","Ugyldig luftfuktigheitsdata rom B.")
            else:
                logger.info('Humid B: ' + str(humidity))
                mqttc.publish("adam4017/humidityB", humidity)
           
            temperature = (-40 + (sensor.readAnalogIn(3)-4) * 7.5) + 1
            temperature = float('{0:.1f}'.format(temperature))
            
            if (temperature < 0) or (temperature > 70):
                logger.warning('Invalid temperature data room B: ' + str(temperature))
                mqttc.publish("adam4017/temperatureB", -1)
                mqttc.publish("adam4017/temperatureB", "Ugyldig temperaturdata rom B")
            else:
                logger.info('Temp A: ' + str(temperature))
                mqttc.publish("adam4017/temperatureB", temperature)
 
#            humidity = ((sensor.readAnalogIn(2)-4) * 6.25) + 1
#            humidity = float('{0:.1f}'.format(humidity))
#            
#            logger.info('Humid B: ' + str(humidity))
#           
#            temperature = (-40 + (sensor.readAnalogIn(3)-4) * 7.5) + 1
#            temperature = float('{0:.1f}'.format(temperature))
#            
#            logger.info('Temp B: ' + str(temperature))
#            
#            mqttc.publish("adam4017/temperatureB", temperature)
#            mqttc.publish("adam4017/humidityB", humidity)
           
            time.sleep(5)

    except KeyError:
        logger.error('Invalid configuration file')
    except Exception, e:
        logger.error('Failed', exc_info=True)
        raise


if __name__ == '__main__':
    #try:
    main()
    #except KeyboardInterrupt:
        #logger.info('Keyboard interrupt')
