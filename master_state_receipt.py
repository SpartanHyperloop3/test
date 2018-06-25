"""METHOD 1- CHANGE LOGIC IN THE ORIGINAL THREAD"""

#replace from line 59 in master_sm code with line 32-51 here

#JSON sample:

"""
{

    "PC": {
        "reading": 13,
        "time": null,
        "units": "PC"
}
"""

class incomingDataThread(threading.Thread):
    """Retrieves incoming data from all subscribed devices.
    Continuously runs in the background collecting data from slaves.
    Data is assumed to be in a list form with two entries, a string
    in the first entry that signifies the sensor or input from which
    the reading came, and a numerical value as the second entry. The
    second entry can be floating point. The thread puts the sensor name
    in a storage object of type dataController and also updates a work
    queue with name of the sensor which was updated. The work queue is later
    consumed by another thread to check if the new reading which was entered
    will have changed the corresponding logic associated with the sensor value
    or input value.
    """

    def __init__(self, control, zmqSock):
        """incomingDataThread constructor.
        Args:
            control: must pass outer class object to obtain access to methods.
            zmqSock: current socket for incoming data
        """
        threading.Thread.__init__(self)
        self._killFlag = threading.Event()
        self.control = control
        self.sock = zmqSock
        self.poller = zmq.Poller()
        self.poller.register(self.sock, zmq.POLLIN)

    def run(self):
        while not self._killFlag.is_set():
            if self.poller.poll(1000):
                message = self.sock.recv_json()

                if self.control.rawDataUnits["PC"]!="PC":
                    self.sock.send_json(["state", self.control.rawDataReading["PC"]])
                else:
                    # print self.control.rawData.getCurrentReadingFor("PI_1_U1_CH4")
                    # print self.control.rawData.getCurrentTimeForAsc("PI_1_U1_CH1")
                    # print self.control.rawDataUnits["PI_1_U1_CH1"]
                    self.control.sendDataToControlStation(self.sock)
                    self.control.rawData.updateEntry(message[0], [message[1], message[2]])

                    # print self.control.rawData.getCurrentReadingFor(message[0])
                    self.control.inputLogicQueue.put(message[0])

    def stop(self):
        self._killFlag.set()




################################################################################
####################################    OR  ####################################
################################################################################


#   METHOD 2: CREATE NEW LISTENING THREAD FOR LAPTOP

class incomingDataThreadPC(threading.Thread):
    """Retrieves incoming data from PC
    """

    def __init__(self, control, zmqSock):
        """incomingDataThread constructor.
        Args:
            control: must pass outer class object to obtain access to methods.
            zmqSock: current socket for incoming data from PC
        """
        threading.Thread.__init__(self)
        self._killFlag = threading.Event()
        self.control = control
        self.sock = zmqSock
        self.poller = zmq.Poller()
        self.poller.register(self.sock, zmq.POLLIN)

    def run(self):
        while not self._killFlag.is_set():
            if self.poller.poll(1000):
                message = self.sock.recv_json()

                if self.control.rawDataUnits["PC"]!="PC":
                    self.sock.send_json(["state", self.control.rawDataReading["PC"]])
                else:
                    # print self.control.rawData.getCurrentReadingFor("PI_1_U1_CH4")
                    # print self.control.rawData.getCurrentTimeForAsc("PI_1_U1_CH1")
                    # print self.control.rawDataUnits["PI_1_U1_CH1"]
                    self.control.sendDataToControlStation(self.sock)
                    self.control.rawData.updateEntry(message[0], [message[1], message[2]])

                    # print self.control.rawData.getCurrentReadingFor(message[0])
                    self.control.inputLogicQueue.put(message[0])

    def stop(self):
        self._killFlag.set()




