#!./bin/python3
# https://github.com/guyc/py-gaugette
# https://guy.carpenter.id.au/gaugette/2013/01/14/rotary-encoder-library-for-the-raspberry-pi/
# logging https://realpython.com/python-logging/
import time
import sys
import os
import signal
from dotenv import load_dotenv
import logging
import systemd.daemon
import gaugette.gpio
import gaugette.rotary_encoder
import gaugette.switch
import pyOpenHabComm
from datetime import datetime, timedelta

# TODO\
# Improve Lamp and Encode classes
# setup: dedicated service user
# Incorporate encoder sw


# Logger: logging config   https://docs.python.org/3/howto/logging-cookbook.html
# Create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('[%(asctime)s] [%(levelname)-5s] [%(name)s] - %(message)s')

# .env import
## Find script directory
## https://stackoverflow.com/a/9350788
envLoc = os.path.dirname(os.path.realpath(__file__)) + "/.env"
# Test if exist then import .env
if not os.path.exists(envLoc):
  logging.error(".env file not found")
  logging.debug("envLoc value: %r" % envLoc)
  sys.exit(1)
try:
  load_dotenv(envLoc)  # loads .env file in current directoy
except:
  logging.error("Error loading .env file")
  sys.exit(1)

# Logger: create console handle - Note: not needed when using as a systemd service
if os.getenv('LOGGING_ENABLE_CONSOLE') == 'True':
  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)     # set logging level for consol
  ch.setFormatter(formatter)
  logger.addHandler(ch)

# Logger: create systemd Journal handler
if os.getenv('LOGGING_ENABLE_JOURNAL') == 'True':
  from systemd import journal
  jh = systemd.journal.JournalHandler()
  jh.setLevel(logging.INFO)
  j_formatter = logging.Formatter('[%(levelname)-5s] [%(threadName)s][%(name)s] - %(message)s')   # Journaling already tracks 'time host service: '
  jh.setFormatter(j_formatter)
  logger.addHandler(jh)

# Logger: create file handler
if os.getenv('LOGGING_ENABLE_FILE') == 'True':
  SERVICE_LOG_PATH=os.getenv('SERVICE_LOG_PATH') + "lamp.log"
  logging.debug ("Service Log path: %r" % SERVICE_LOG_PATH)
  fh = logging.FileHandler(SERVICE_LOG_PATH, mode='a') # w while testing
  fh.setFormatter(formatter)     # set format
  fh.setLevel(logging.DEBUG)     # set level for file logging
  logger.addHandler(fh)          # add filehandle to logger

# reduce logging level of libraries
logging.getLogger("pyOpenHabComm").setLevel(logging.INFO)
logging.getLogger("schedule").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)   # used by requests. cuts out 'connectionpool' logs

UPDATE_RATE =   float(os.getenv('UPDATE_RATE'))

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
    # Fast or slow rate based on how much encoder was popped
    xA = abs(x)
    if xA < 7:
        logging.debug ("Delta mod normal")
        mod = mod * 1.5
    else:
        logging.debug ("Delta mod fast")
        mod = mod * 3
    new = self.value + x * mod
    if new > 100:
      new = 100
    if new < 0:
      new = 0
    logging.debug ("curv: %d mod: %f x: %d xm: %f Newr: %f  Newd: %d" % (self.value,mod,x,x*mod,new,int(new)))
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
    #logging.debug ("Caklback> x: %d delta: %d" %(x,self.delta))

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

active = 0    # Initialize to inactive
activeTimeout = 0

# setup openhab object
OH = pyOpenHabComm.OPENHABCOMM(url=os.getenv('URL'), user=os.getenv('User'), pw=os.getenv('Pass'))
Item = os.getenv('OHItem')

# Signal handling
killNow = False
def handler_stop_signals(signum, frame):
  global killNow
  killNow = True
  logging.debug("Stop signal received: %r" % signum)
signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

# Main()
logging.info("Script started")
systemd.daemon.notify('READY=1')
while not killNow:
  systemd.daemon.notify('WATCHDOG=1')
  try:
    active = en.active

    # Active edge
    if active and not activeTimeout > 0:   # Note: active could be false while still within activeTimeout period
      logging.info("Encoder now active")
      cur = OH.getItemStatus(Item) # get current value from OpenHab
      if cur is not None:
        logging.debug("Current item val: %s" % cur)
        logging.info("Current lamp val: %s" % cur['state'])
        # update lamp with latest value from server
        lamp.setvalue(int(cur['state']))
      else: # if cur is None
        logging.warning("Could not get a value from OH. Setting to 50")
        lamp.setvalue(50)

    # Actions when active
    if active: # activeTimeout > 0:  # Fast polling when activly being used
      activeTimeout = float(os.getenv('ACTIVETIMEOUT'))
      delta = en.popDelta()
      logging.debug ("Delta popped was: %d" % delta)
      if delta != 0:
        lamp.add(delta)
        # Send to openhab
        OH.sendItemCommand(Item, lamp.value)
        logging.info("Sent %d to server" % lamp.value)

    if activeTimeout > 0:
      #logging.debug("Actives: %r, %f" % (active, activeTimeout))
      activeTimeout = activeTimeout - UPDATE_RATE
    time.sleep(UPDATE_RATE)

  except KeyboardInterrupt:
    logging.info("Shutdown requested...exiting")
    systemd.daemon.notify('STOPPING=1')
    logging.shutdown()
    sys.exit(0)
  except Exception as e:
    logging.error("Exception in main: %r" % e)
    sys.exit(1)

# cleanup
logging.info("Shutdown requested...exiting")
systemd.daemon.notify('STOPPING=1')
logging.shutdown()
sys.exit(0)
