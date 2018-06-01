import logging
import time

import network

LOCAL_IP = "192.168.3.10"

'''
def output:
    network_test.
'''

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.debug(network.SERVER_HOST)
network.SERVER_HOST = LOCAL_IP
logging.debug(network.SERVER_HOST)

network_test = network.Connection()
logging.debug(network_test.isConnected())
#network_test.wait(whenHearCall=output)
while True:
    time.sleep(2)
    logging.debug(network_test.isConnected())
#another small change