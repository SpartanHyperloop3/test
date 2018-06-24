import threading
import os
import time

class NetworkWatchdogSslave(threading.Thread):

    """
    Pings the master pi periodically to check for network disconnection, thus working as a co-master.
    In case of a single point of error, emergency command to the slaves is sent.
    """

    def __init__(self, control):                            #check with Brad about control arg
        threading.Thread.__init__(self)
        self._killFlag = threading.Event()
        self.control = control

    def run(self):
        ips_list = ["192.168.3.13"]                         #enter the masterr's ip
        while not self._killFlag.is_set():
            try:
                for ip in ips_list:
                    response = os.system("ping -i 1 -n 1 -l 1 " + ip + " -w 5")
                    time.sleep(1)
                    if response == 0:
                        print(ip, 'is up!')
                    else:                                   #remove else once if function is done
                        print(ip, 'is down!')


#for self-class test, uncomment:
"""
    while True:
        os.system("cls")
        run()
"""
