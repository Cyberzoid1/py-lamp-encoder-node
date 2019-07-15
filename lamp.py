#!./bin/python3
# https://github.com/guyc/py-gaugette
# https://guy.carpenter.id.au/gaugette/2013/01/14/rotary-encoder-library-for-the-raspberry-pi/
# logging https://realpython.com/python-logging/
import time
import sys
import os
from dotenv import load_dotenv
import threading
import logging
import gaugette.gpio
import gaugette.rotary_encoder
import gaugette.switch
import pyOpenHabComm
from datetime import datetime, timedelta

# debugging
# https://realpython.com/python-debugging-pdb/
import pdb
# set tracepoint with pdb.set_trace()


# TODO
# fix logger
# term signal handling
# notiice signal sending for future systemd service
# File logging?? (or just use logger)
# Improve Lamp and Encode classes
# traceback error in main



# Logging setup
#logger = logging.getLogger()
#ormater
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(threadName)s - %(message)s')
#logger.setLevel(DEBUG)
logging.info ("Start")
logging.info ("test")
logging.debug ("debug")

# .env import
if not os.path.exists("./.env"):
  logging.error(".env file not found")
  sys.exit(1)
try:
  load_dotenv()  # loads .env file in current directoy
except:
  logging.error("Error loading .env file")
  sys.exit(1)

UPDATE_RATE =   float(os.getenv('UPDATE_RATE'))
ACTIVE_RATE =   float(os.getenv('ACTIVE_RATE'))
INACTIVE_RATE = float(os.getenv('INACTIVE_RATE'))

# Lamp item object & methods
class LAMP:
  value = None # current live value of the lamp
  value = 20
  def __init__(self, name=None):
    if name is None:
      raise "Lamp needs itemname"
    self.name = name
  def setvalue(self, x):
    if x < 0:
      x = 0
    elif x > 100:
      x = 100
    self.value = x
    logging.info("Lamp value set to: %d" % self.value)
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


# encoder wrapper class for delta handling
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


# lamp & encoder setup
lamp = LAMP(os.getenv('OHItem'))
en = ENCODE(CLK=int(os.getenv('A_PIN')), DT=int(os.getenv('B_Pin')))

# worker thread that updates the OpenHab server
def update_lamp():
  # setup openhab object
  OH = pyOpenHabComm.OPENHABCOMM(url=os.getenv('URL'), user=os.getenv('User'), pw=os.getenv('Pass'))
  Item = os.getenv('OHItem')
  while True:
    if eventActive.isSet():
      logging.debug ("Sleepting -update")
      print ("Sleepting -update")
      time.sleep(UPDATE_RATE) # Active wait x seconds between updates
    else:
      logging.debug ("Blocked")
      print("Blocked")
      time.sleep(.1)
      eventActive.wait()  # wait till unblocked. aka active
      cur = OH.getItemStatus(Item) # get current value
      logging.debug("Current item val: %s" % cur)
      logging.info("Lamp val: %s" % cur['state'])
      # update lamp with latest value from server
      lamp.setvalue(int(cur['state']))
    
    delta = en.popDelta()
    logging.debug ("Delta popped was: %d" % delta)
    lamp.add(delta)
    if delta != 0:
      # TODO Send to openhab
      # OH.sendItemCommand(Item, lamp.value)
      logging.info("Sent %d to server" % lamp.value)
    logging.debug(eventActive.isSet())
    print ("Was here")

# Thread setup
eventActive = threading.Event()
tUpdateLamp = threading.Thread(target=update_lamp, name="update lamp", daemon=True)
tUpdateLamp.start()
active = 0    # Initialize to inactive
activeTimeout = 0

# Main()
while True:
  try:
    activeLast = active
    active = en.active
    
    if active and not activeLast:
      activeTimeout = float(os.getenv('ACTIVETIMEOUT'))
      print ("Active timeout is: %f" % activeTimeout)

    logging.info ("%d: curr delta: %d  Atimout: %f" % (active,en.delta, activeTimeout))

    # Determin how long to poll/sleep.
    if activeTimeout > 0:  # Fast polling when activly being used
      time.sleep(ACTIVE_RATE)
      eventActive.set()
      activeTimeout = activeTimeout - ACTIVE_RATE
    else:       # Slower polling to reduce CPU usage when inactive
      eventActive.clear()
      time.sleep(INACTIVE_RATE)

  except KeyboardInterrupt:
    logging.info("Shutdown requested...exiting")
    sys.exit(0)
  except Exception:
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)
