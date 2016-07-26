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

import argparse

import paho.mqtt.client as mqtt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():

    print("Analog inputs:")	

    logger.info('Creating instance of ADAM4017 class.')
    sensor = adam4017('/dev/ttyUSB1',1)

    mqttc = mqtt.Client()

    print('Configuration: ' + sensor.readConfiguration())	
    print('Firmware version: ' + sensor.readFirmwareVersion())	
    print('Module name: ' + sensor.readModuleName())	
    
    print('AI0: ' + str(sensor.readAnalogIn(0)))
    print('AI1: ' + str(sensor.readAnalogIn(1)))
    print('AI2: ' + str(sensor.readAnalogIn(2)))
    print('AI3: ' + str(sensor.readAnalogIn(3)))

    logger.info('Connecting to MQTT')
    mqttc.connect("localhost")
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


class adam4017:
    def __init__(self, serialPort, address):
        self.serialPort = serialPort
        self.address = address

	self.ser = serial.Serial('/dev/ttyUSB1', timeout=0.1)
	
	#ser = serial.rs485.RS485('/dev/ttyUSB1', timeout=0.1)
	#ser.rs485_mode = serial.rs485.RS485Settings()
	
	self.ser.bytesize = serial.EIGHTBITS #number of bits per bytes
	self.ser.parity = serial.PARITY_NONE #set parity check: no parity
	self.ser.stopbits = serial.STOPBITS_ONE #number of stop bits
	self.ser.xonxoff = False    #disable software flow control
	self.ser.rtscts = False    #disable hardware (RTS/CTS) flow control
	self.ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
	self.ser.writeTimeout = 2     #timeout for write
	
	self.ser.baudrate = 9600

    	self.address = hex(address).replace("0x","")
    	self.address = "0" + self.address.upper()	

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
	self.ser.close()
    
    def readAnalogIn(self, port):
    	command = ('#' + self.address + str(port))
    	
        checksum = self.computeChecksum(command)	
	command = (command + checksum + '\r')
	logger.info('Command: ' + command)

        return float(self.send(command)[2:8])

    def readConfiguration(self):
        command = ('$' + self.address + '2')
    
        # Response is !AATTCCFF(cr)
        # Where AA is module address
	
        checksum = self.computeChecksum(command)	
	command = (command + checksum + '\r')
	logger.info('Command: ' + command)
        return self.send(command)

    def readFirmwareVersion(self):
        logging.info('Enquiring firmware version')
        command = ('$' + self.address + 'F')
    	
        checksum = self.computeChecksum(command)	
	command = (command + checksum + '\r')
	
        logger.info('Command: ' + command)
       
        return self.send(command)

    def readModuleName(self):
        logging.info('Enquiring module name')
        command = ('$' + self.address + 'M')
    	
        checksum = self.computeChecksum(command)	
	command = (command + checksum + '\r')
	logger.info('Command: ' + command)

        return self.send(command)

    def send(self, data):
        logger.info('Sending command to module')
	self.ser.rts = True
	self.ser.write(data)

        # Sleep the time it takes for the UART to transmit the data 	
	time.sleep(0.008)
	self.ser.rts = False

        response = self.ser.readline()
        logger.info('RAW: ' + response)
	return response


    def computeChecksum(self, data):
	checksum = 0
        for code in bytearray(data):
		checksum += code
	checksum = checksum % 0x100
 
	logger.debug('Checksum: ' + str(checksum))
	logger.debug('Checksum: ' + str(hex(checksum)))
	       
        return str(hex(checksum)).replace("0x","").upper() 

if __name__ == '__main__':
	main()
