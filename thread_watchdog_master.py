import threading
import os
import time

class NetworkWatchdogMaster(threading.Thread):

    """
    Pings each of the slave pi's and the off-pod laptop periodically to check for network disconnection
    In case of a single point of error, emergency command to the slaves is sent.
    """

    def __init__(self, control):                            #check with Brad about control arg
        threading.Thread.__init__(self)
        self._killFlag = threading.Event()
        self.control = control

    def run(self):
        ips_list = ["192.168.3.14", "192.168.3.15", "192.168.3.16", "192.168.3.17", "192.168.0.0"]
        while not self._killFlag.is_set():
            try:
                for ip in ips_list:
                    response = os.system("ping -i 1 -n 1 -l 1 " + ip + " -w 5")
                    time.sleep(1)
                    if response == 0:                       #change print function to broadcast state 13
                        print(ip, 'is up!')
                    else:                                   #remove else once if function is done
                        print(ip, 'is down!')


#for self-class test, uncomment:
"""
    while True:
        os.system("cls")
        run()
"""
