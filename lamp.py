#!./bin/python3
# https://github.com/guyc/py-gaugette
# https://guy.carpenter.id.au/gaugette/2013/01/14/rotary-encoder-library-for-the-raspberry-pi/
# logging https://realpython.com/python-logging/
import time
import threading
import logging
import gaugette.gpio
import gaugette.rotary_encoder
import gaugette.switch
import pyOpenHabComm
from datetime import datetime, timedelta

# TODO
# fix logger
# better event name
# better thread name
# rip items out of openhab library. Just the openhab server. pass item, value & type
# review active state
# keyboard interrupt handling
# term signal handling
# notiice signal sending for future systemd service
# File logging?? (or just use logger)
# Improve Lamp and Encode classes
# env file



# Logging setup
#logger = logging.getLogger()
#ormater
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(threadName)s - %(message)s')
#logger.setLevel(DEBUG)
logging.info ("Start")
logging.info ("test")
logging.debug ("debug")


# Pins
A_PIN = 7
B_PIN = 9

UPDATE_RATE = 5
ACTIVE_RATE = .5
INACTIVE_RATE = 3

class LAMP:
  value = None # current live value of the lamp
  value = 20
  def __init__(self, name=None):
    if name is None:
      raise "Lamp needs itemname"
    self.name = name
  def add(self, x):
    mod = self.transform(self.value)
    new = self.value + x * mod
    if new > 100:
      new = 100
    if new < 0:
      new = 0
    print ("curv: %d mod: %f x: %d xm: %f Newr: %f  Newd: %d" % (self.value,mod,x,x*mod,new,int(new)))
    self.value = int(new)

  # Scales input based on current value
  def transform(self, x):
    # https://mycurvefit.com/
    # Data:
    # 1                1          
    # 10                1.1        
    # 20                1.3        
    # 40                1.7        
    # 50                2          
    # 75                3          
    #100                3    
    a = 3.180
    b = 1.122
    c = 3.180
    d = 51.022
    e = 4.451399
    mod = a + (b - c)/(1 + (x / d)**e)
    return mod



class ENCODE:
  delta = 0
  active = 0
  def __init__(self, CLK=None, DT=None, SW=None):
    self.gpio = gaugette.gpio.GPIO()
    self.encoder = gaugette.rotary_encoder.RotaryEncoder(self.gpio, CLK, DT, callback=self.callback)
    self.encoder.start()
    #self.sw = gaugette.switch.Switch(self.gpio, SW)

  # Interrupt callback from gaugette lib
  def callback(self, x):
    self.delta = self.delta + x
    self.active = 1
    #logging.debug ("x: %d delta: %d" %(x,self.delta))

  def resetDelta(self):
    self.delta  = 0
    self.active = 0 # set to inactive
  
  # returns & clears delta
  def popDelta(self):
    d = self.delta
    self.delta  = 0
    self.active = 0 # set to inactive
    return d
  
  # return delta
  def getdelta(self):
    return self.delta
  
  def get_cycles(self):
    return self.encoder.get_steps()



lamp = LAMP("testitem")
en = ENCODE(CLK=A_PIN, DT=B_PIN)


def update_lamp():
  while True:
    delta = en.popDelta()
    logging.debug ("Delta popped was: %d" % delta)
    # TODO Send to openhab
    logging.debug(e.isSet())
    print ("Why")

    if e.isSet():
      print ("sleepting -update")
      time.sleep(UPDATE_RATE) # Active wait x seconds between updates
    else:
      logging.debug ("Blocked")
      print("Blocked")
      time.sleep(.1)
      e.wait()  # wait till unblocked. aka active

e = threading.Event()
t = threading.Thread(target=update_lamp, name="update lamp",)
t.start()
active = 0    # Initialize to inactive



while True:
  activeLast = active
  active = en.active

  logging.info ("%d: curr delta: %d" % (active,en.delta))



  # Determin how long to poll/sleep.
  if active:  # Fast polling when activly being used
    time.sleep(ACTIVE_RATE)
    e.set()
  else:       # Slower polling to reduce CPU usage when inactive
    e.clear()
    time.sleep(INACTIVE_RATE)
