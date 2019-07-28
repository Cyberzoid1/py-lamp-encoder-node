
import requests
import logging
import json

# Create Logger. Name will be the filename 'pyOpenHabComm'
OHLogger = logging.getLogger(__name__)

class OPENHABCOMM():
    def __init__(self, url=None, user=None, pw=None, datatype=str):
        if url is None:
            raise "Must supply a URL"
        self.url = url
        self.user = user
        self.pw = pw
        self.datatype = datatype

    def sendItemCommand(self, item, data):
        OHLogger.debug ("Sending %r type %r to item %r" % (data, type(data), item))

        # Send activity to server
        try:
            myresponce = requests.post(self.url + 'items/' + item, data, auth=(self.user,self.pw), timeout=3.0)
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

    h.sendItemCommand(I,"ON")
    sleep(.250)
    OHLogger.info(h.getItemStatus(I))
    sleep(.250)
    h.sendItemCommand(I,"OFF")
    sleep(.250)
    OHLogger.info(h.getItemStatus(I))
