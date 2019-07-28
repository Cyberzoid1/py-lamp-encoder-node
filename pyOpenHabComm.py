
import requests
import logging
import json

# Create Logger. Name will be the filename 'pyOpenHabComm'
OHLogger = logging.getLogger(__name__)
OHLogger.setLevel(logging.DEBUG) # default level

class OPENHABCOMM():
    def __init__(self, url=None, user=None, pw=None, datatype=str):
        if url is None:
            raise "Must supply a URL"
        self.url = url
        self.user = user
        self.pw = pw
        self.datatype = datatype

    def sendItemCommand(self, item, data):
        OHLogger.debug ("Sending %r type %r to item %r (auto converting to str)" % (data, type(data), item))

        # Send activity to server
        try:
            myresponce = requests.post(self.url + 'items/' + item, str(data), auth=(self.user,self.pw), timeout=3.0)
            OHLogger.debug("Return value: %r" % myresponce.text)
        except (requests.ConnectTimeout, requests.ConnectionError) as e:
            OHLogger.error ("Connection error")
            OHLogger.error(str(e))
        except (requests.ReadTimeout, requests.Timeout) as e:
            OHLogger.error ("Request Timedout")
            OHLogger.error(str(e))
        except requests.RequestException as e:
            OHLogger.error ("Request: General Error")
            OHLogger.error (str(e))

    def getItemStatus(self, item):
        try:
            myresponce = requests.get(self.url + 'items/' + item, auth=(self.user,self.pw), timeout=3.0)
            OHLogger.debug("Item value: %r" % myresponce.text)
            return myresponce.json()
        except (requests.ConnectTimeout, requests.ConnectionError) as e:
            OHLogger.error ("Connection error")
            OHLogger.error(str(e))
        except (requests.ReadTimeout, requests.Timeout) as e:
            OHLogger.error ("Request Timedout")
            OHLogger.error(str(e))
        except requests.RequestException as e:
            OHLogger.error ("Request: General Error")
            OHLogger.error (str(e))
        

# Testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    OHLogger.info("pyOPenHabComm test script started")
    from time import sleep
    from dotenv import load_dotenv
    import os

    if not os.path.exists("./.env"):
        OHLogger.error(".env file not found")
        sys.exit(1)
    try:
        load_dotenv(verbose=True)  # loads .env file in current directoy
    except:
        OHLogger.error("Error loading .env file")
        sys.exit(2)
    U = os.getenv('URL')
    I = os.getenv('OHItem')
    h = OPENHABCOMM(U, os.getenv('User'), os.getenv('Pass'))

    h.sendItemCommand(I,"67")  # Turn on to 67%
    sleep(.250)
    OHLogger.info(h.getItemStatus(I))
    sleep(1.250)
    h.sendItemCommand(I,"0")    # Turn off
    sleep(.250)
    OHLogger.info(h.getItemStatus(I))
