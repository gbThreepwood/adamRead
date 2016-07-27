#!/usr/bin/python
# Communication script for ADAM4017 using ADAM4561 USB to RS485 converter
# 
# TODO: Add support for the other modules in the ADAM 4000 series
#
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
#import io
import time
import datetime

#import argparse

#import paho.mqtt.client as mqtt
import logging

##logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)
#
## create a file handler
#handler = logging.FileHandler('adamRead.log')
#handler.setLevel(logging.INFO)
#
## create a logging format
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#handler.setFormatter(formatter)
#
## add the handlers to the logger
#logger.addHandler(handler)
#

logger = logging.getLogger(__name__) 

class adam4017:
    def __init__(self, serialPort, address):
        self.serialPort = serialPort
        self.address = address

        try:
    	    self.ser = serial.Serial(self.serialPort, timeout=0.1)
    	    
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

        except serial.serialutil.SerialException:
            logger.error('Could not open serial port')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
	self.ser.close()
    
    def readAnalogIn(self, port):
    	command = ('#' + self.address + str(port))
    	
        checksum = self.computeChecksum(command)	
	command = (command + checksum + '\r')
	logger.info('Command: ' + command)

        response = self.send(command)

        # The response should start with a >
        # and have a length of 8 bytes + checksum + (cr)

        try:
            start = response.index('>')
            end = response.index('\r')
    
            logger.debug('Start index: ' + str(start))
            logger.debug('End index: ' + str(end))
    
            response_checksum = response[end - 2:end]
            logger.info('Response checksum: ' + response_checksum)
    
            response_data = response[start:end - 2]
            logger.info('Response data: ' + response_data)
    
            computed_checksum = self.computeChecksum(response_data)
            logger.info('Computed checksum: ' + computed_checksum)      
     
            if (int(response_checksum,16) != int(computed_checksum,16)):
                logger.warning('Checksum mismatch')
                return -1
            else:
                logger.info('Checksum passed')
                
                data =  float(response[start + 1:8])
                logger.info('Extracted data: ' + str(data))
                return data
        except:
            logger.warning('Invalid data received')
            return -1
    
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
        logger.debug('Enabling line driver')
	self.ser.rts = True
	self.ser.write(data)

        # Sleep the time it takes for the UART to transmit the data 	
	time.sleep(0.008)
        logger.debug('Disabling line driver')
	self.ser.rts = False

        response = self.ser.readline()
        logger.info('RAW data response: ' + response)
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
   print('This is a library') 
