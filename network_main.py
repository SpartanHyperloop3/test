import logging
import time

import network

SERVER_IP = "192.168.3.10"
DEVICE = "server"

def output():
    logging.debug("output function")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.debug(network.SERVER_HOST)
network.SERVER_HOST = SERVER_IP
logging.debug(network.SERVER_HOST)

network_test = network.Connection()
logging.debug(network_test.isConnected())
if DEVICE == "server":
    network_test.wait(whenHearCall=output)
else:
    network_test.call(SERVER_IP, whenHearCall=output)

while True:
    time.sleep(2)
    logging.debug(network_test.isConnected())
