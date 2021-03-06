#!/usr/bin/python
import requests
import socket
import threading
import logging
import RPi.GPIO as GPIO
#import mraa

 # change this to the values from MCS web console
DEVICE_INFO = {
     'device_id' : 'DjvCl4cU',
     'device_key' : 'ImSnUDXI0709NjfS'
 }

 # change 'INFO' to 'WARNING' to filter info messages
logging.basicConfig(level='INFO')

heartBeatTask = None

def establishCommandChannel():
     # Query command server's IP & port
     connectionAPI = 'https://api.mediatek.com/mcs/v2/devices/%(device_id)s/connections.csv'
     r = requests.get(connectionAPI % DEVICE_INFO,
                  headers = {'deviceKey' : DEVICE_INFO['device_key'],
                             'Content-Type' : 'text/csv'})
     logging.info("Command Channel IP,port=" + r.text)
     (ip, port) = r.text.split(',')

     # Connect to command server
     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     s.connect((ip, int(port)))
     s.settimeout(None)

     # Heartbeat for command server to keep the channel alive
     def sendHeartBeat(commandChannel):
         keepAliveMessage = '%(device_id)s,%(device_key)s,0' % DEVICE_INFO
         commandChannel.sendall(keepAliveMessage)
         logging.info("beat:%s" % keepAliveMessage)

     def heartBeat(commandChannel):
         sendHeartBeat(commandChannel)
         # Re-start the timer periodically
         global heartBeatTask
         heartBeatTask = threading.Timer(40, heartBeat, [commandChannel]).start()

     heartBeat(s)
     return s

def waitAndExecuteCommand(commandChannel):
     while True:
         command = commandChannel.recv(1024)
         logging.info("recv:" + command)
         # command can be a response of heart beat or an update of the LED_control,
         # so we split by ',' and drop device id and device key and check length
         fields = command.split(',')[2:]

         if len(fields) > 1:
             timeStamp, dataChannelId, commandString = fields
             if dataChannelId == 'LEDControl':   #cloud name
                 # check the value - it's either 0 or 1
                 commandValue = int(commandString)
                 logging.info("led :%d" % commandValue)
                 setLED(commandValue)

pin = None
def setupLED():
     global pin

     GPIO.setmode(GPIO.BCM) #led
     GPIO.setup(23,GPIO.OUT)


     # on LinkIt Smart 7699, pin 44 is the Wi-Fi LED.
 #    pin = mraa.Gpio(44)
 #   pin.dir(mraa.DIR_OUT)

def setLED(state):
     # Note the LED is "reversed" to the pin's GPIO status.
     # So we reverse it here.
     if state:       	#led control
         GPIO.output(23,1)
     else:
         GPIO.output(23,0)

if __name__ == '__main__':
     setupLED()
     channel = establishCommandChannel()
     waitAndExecuteCommand(channel)
