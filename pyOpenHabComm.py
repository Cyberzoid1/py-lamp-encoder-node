
import requests
import logging

logging.basicConfig(level=logging.info)

class OPENHABCOMM():
    def __init__(self, url=None, user=None, pw=None, datatype=str):
        if url is None:
            raise "Must supply a URL"
        self.url = url
        self.user = user
        self.pw = pw
        self.datatype = datatype

    def sendItemCommand(self, item, data):
        logging.debug ("Sending %r type %r to item %r" % (data, type(data), item))

        # Send activity to server
        try:
            myresponce = requests.post(self.url + 'items/' + item, data, auth=(self.user,self.pw), timeout=3.0)
        except (requests.ConnectTimeout, requests.ConnectionError) as e:
            logging.error ("Connection error")
            logging.error(str(e))
        except (requests.ReadTimeout, requests.Timeout) as e:
            logging.error ("Request Timedout")
            logging.error(str(e))
        except requests.RequestException as e:
            logging.error ("Request: General Error")
            logging.error (str(e))
        else:
            logging.info (myresponce.text)

    def getItemStatus(self, item):
        try:
            #logging.debug("u: %s   p: %s" % (self.user, self.pw))
            myresponce = requests.get(self.url + 'items/' + item, auth=(self.user,self.pw), timeout=3.0)
        except (requests.ConnectTimeout, requests.ConnectionError) as e:
            logging.error ("Connection error")
            logging.error(str(e))
        except (requests.ReadTimeout, requests.Timeout) as e:
            logging.error ("Request Timedout")
            logging.error(str(e))
        except requests.RequestException as e:
            logging.error ("Request: General Error")
            logging.error (str(e))
        else:
            logging.info (myresponce.text)
        logging.debug("Item value: %r" % myresponce)
        return myresponce


# Testing
if __name__ == "__main__":
    from time import sleep
    U = "https://example.com/rest/"
    I = "testswitch"
    h = OPENHABCOMM(U,'user','password')

    h.sendItemCommand(I,"ON")
    sleep(.250)
    logging.info(h.getItemStatus(I))
    sleep(.250)
    h.sendItemCommand(I,"OFF")
    sleep(.250)
    logging.info(h.getItemStatus(I))
