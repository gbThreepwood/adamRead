#!/usr/bin/python
# Communication script for ADAM4017 using ADAM4561 USB to RS485 converter
# Eirik Haustveit, 2016

# In order to communicate with the RS485 bus the RTS line needs to be controlled.
# When RTS is true the line drivers are enabled, i.e. the converter is in TX mode.
#
# In order to receive data the line driver must be disabled by setting the
# RTS line low(false). The timing of this change is critical, the state must
# not change to false before the transmission is completed, but it must change before
# the slave starts transmitting a response.
#
#
# Version 3 of the pySerial library supports a special RS485 mode, where the timing
# is handled automatically

import serial
import io
import time
import datetime

import argparse
import configparser


import paho.mqtt.client as mqtt
import logging

from adam4000 import adam4017

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('adamRead.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)



def main():
    try:
        config = configparser.ConfigParser()
        config.read('adamread.conf')

        now = datetime.datetime.now()

        logger.info('Program executed at: %s ' % now.isoformat())

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
            logger.info('Humid A: ' + str(humidity))
           
            temperature = -40 + (sensor.readAnalogIn(1)-4) * 7.5
    
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
           
            time.sleep(1)

    except KeyError:
        logger.error('Invalid configuration file')
    except:
        raise


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt')
