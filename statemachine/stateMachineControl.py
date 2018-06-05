import zmq
import time
import threading
import sys
import commitLog
import dataController
import json
import Queue
import logging
import copy

logging.basicConfig(level=logging.DEBUG,
                   format='(%(threadName)-10s) %(message)s',)


class stateMachineControl(object):
    """State machine control thread.

    This class contains all of the methods and sub-classes necessary to
    handle incoming data. The controller takes the raw data and applies
    corresponding logic to produce boolean values that are used to determine
    the next the state to transistion to. Once the state has changed the controller
    broadcasts the change to all connected datapath devices.
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

        def run(self):
            while not self._killFlag.is_set():
                message = self.sock.recv_json()
                self.control.rawData.updateEntry(message[0], message[1])
                self.control.inputLogicQueue.put(message[0])

        def stop(self):
            self._killFlag.set()


    class consumerThread(threading.Thread):
        """reads sensor names from the work queue and updates logic if necessary.

        Runs in the background retrieving the names of sensors currently updated
        by the incomingDataThread. Only the name is needed to retrieve the most 
        current entry by using methods of the dataController class. The sensor 
        reading is ran through logic that has been predetermined in a corresponding
        JSON initialization file. If the current logic entry associated with the 
        sensor reading has updated an event is set to notify the next thread to
        evaluate if the new logic signifies a state change.
        """
        def __init__(self, control):
            """consumerThread constructor.

            Args:
                control: must pass outer class object to obtain access to methods.
            """
            threading.Thread.__init__(self)
            self._killFlag = threading.Event()
            self.control = control

        def run(self):
            while not self._killFlag.is_set():
                dataName = self.control.inputLogicQueue.get(block=True)
                inputStateNameList = self.control.inputLogicNameByDataName[dataName]

                for inputStateName in inputStateNameList:
                    if self.control.setStateInputLogic(inputStateName, dataName):
                        self.control.inputLogicHasBeenUpdated.set()
                        self.control.inputLogicHasBeenUpdated.clear()
                self.control.inputLogicQueue.task_done()

        def stop(self):
            self._killFlag.set()



    class updateStateThread(threading.Thread):
        """Reevaluates current state based on logic.
        
        Waits for the inputLogicHasBeenUpdated event to be set by consumerThread
        which signifies a change in a logic variable. Once the event is set the
        fucntion setNextState of the outer controller class is called to reevaluate
        the state logic. If the state has changed the function setNextState returns
        true and an stateHasChanged is set to notify broadcastStateThread of the change.
        """
        def __init__(self, control):
            """updateStateThread constructor.

            Args:
                control: must pass outer class object to obtain access to methods.
            """
            threading.Thread.__init__(self)
            self._killFlag = threading.Event()
            self.control = control
            self.daemon = True

        def run(self):
            while not self._killFlag.is_set():
                self.control.inputLogicHasBeenUpdated.wait()
                if self.control.setNextState():
                    self.control.stateHasChanged.set()
                    self.control.stateHasChanged.clear()

        def stop(self):
            self._killFlag.set()





    class broadcastStateThread(threading.Thread):
        """Broadcasts state changes to clients.

        If the thread is notified of a state change the new state is sent out
        to all clients.
        """
        def __init__(self, control, zmqSock):
            """broadcastStateThread constructor.

            Args:
                control: must pass outer class object to obtain access to methods.
                zmqSock: current socket for incoming data
            """
            threading.Thread.__init__(self)
            self._killFlag = threading.Event()
            self.control = control
            self.sock = zmqSock
            self.daemon = True

        def run(self):
            while not self._killFlag.is_set():
                self.control.stateHasChanged.wait()
                print "state has changed - sending to slaves - Current State: %s" %self.control.currentState
                self.sock.send_json(["state", self.control.currentState])

        def stop(self):
            self._killFlag.set()





    def __init__(self, setInitialState = 0, stateDataJSONfile = None, inputLogicJSONfile = None, incomingSocket = None, outgoingSocket = None):
        """stateMachineControl constructor.

        Initializes the stateMachineControl object.

        Args:
            setInitialState: set the initial state.

            stateDataJSONfile: JSON file that contains the input logic and current
            state combinations and the state change they signify.

            inputLogicJSONfile: JSON file the contains relates expected raw data from
            clients with the type of logic that should be performed on the data, and the
            name of the logic value that it will be stored in.

            incomingSocket: The socket used for incoming data.

            outgoingSocket: The socket used for outgoing data.
        """

        self.currentState = setInitialState
        
        #events for notifying threads of data changes
        self.inputLogicHasBeenUpdated = threading.Event()
        self.stateHasChanged = threading.Event()
        
        #storage for raw data
        self.rawData = dataController.dataController()
        
        #work queue
        self.inputLogicQueue = Queue.Queue()

        #initialize threads
        self.consumerThread = self.consumerThread(self)
        self.incomingDataThread = self.incomingDataThread(self, incomingSocket)
        self.broadcastStateThread = self.broadcastStateThread(self, outgoingSocket)
        self.stateUpdateThread = self.updateStateThread(self)

        #sockets
        self.incomingSocket = incomingSocket
        self.outgoingSocket = outgoingSocket


        #JSON file parsing begins here, data is extracted for ease of use
        try:
            f = open(stateDataJSONfile, "r")

            stateJSON = json.loads(f.read())

            #validTransitions holds the valid state changes per current state
            self.validTransitions = {}
            arr = []
            for key,val in stateJSON.items():
                for i in val:
                    arr.append(i[0])
                #key is the current state arr holds a list of the valid states
                self.validTransitions[key] = copy.deepcopy(arr)
                del arr[:]


            #statTransitionLogic creates a hash table where the current logic
            #for the current active state can be iterated per valid transistion
            #by creating a key for each list of logic in the for of 
            #[currentstate+validTransistionState]. To explain further, the
            #currentstate is the active state and the validTransitionState
            #is a possible state that can be transitioned to from the current
            #active state. Accessing the key yields a list of known input logic
            #variables and the state, or boolean value (0 or 1), which must be
            #true for the corresponding real boolean value that exists in the 
            #inputLogicState hash table, which is intiliazed in the next section,
            #and constantly updated by the consumerThread.
            self.stateTransitionLogic = {}
            arr = []
            for key,val in stateJSON.items():
                for i in val:
                    self.stateTransitionLogic["%s+%s"%(key,i[0])] = i[1]

            f.close()
        except IOError:
            print "Could not open JSON file"


        try:
            f = open(inputLogicJSONfile, "r")

            cont = json.loads(f.read())

            #inputLogicState holds the current input logic used for next state logic
            self.inputLogicState = {}
            for key,val in cont.items():
                self.inputLogicState[key] = val[0]

            #inputLogicType holds the type of logic, which is used by the 
            #setStateInputLogic method to determine how to process the raw data
            #and report a boolean value to be used for next state logic
            self.inputLogicType = {}
            for key,val in cont.items():
                self.inputLogicType[key] = val[1]["typeOfLogic"]

            #inputLogicUnits holds the units of the data. May be used for future
            #methods when sending data to the control station laptop
            self.inputLogicUnits = {}
            for key,val in cont.items():
                self.inputLogicUnits[key] = val[1]["raw_data_units"]

            #inputLogicParams holds the parameters for the logic type. For example,
            #a list of 2 numbers is used for the upper and lower bounds of a range
            #logic type
            self.inputLogicParams = {}
            for key,val in cont.items():
                for sensor, properties in val[1]["raw_data_names"].items():
                    self.inputLogicParams[key] = properties["params"]

            #inputLogicNameByDataName allows for the input logic variables associated
            #with a rawData value to be found by the rawData name. Because a rawData
            #value may belong to more than one input logic variable (variables found
            #and updated in the inputLogicState hash table) this returns a list.
            #When more than one input logic variable is found it can be iterated, and
            #is done so in the consumerThread to allow for updating each input variable
            #that is associated with the current rawData name taken from the work queue.
            self.inputLogicNameByDataName = {}
            for key,val in cont.items():
                if not val[1]["raw_data_names"]:
                    self.inputLogicNameByDataName[key] = [key]
                for sensor, properties in val[1]["raw_data_names"].items():
                    self.inputLogicNameByDataName.setdefault(sensor, []).append(key)

            #dataValuesPerInputState returns the list of rawData names associated with
            #an input state variable when entered as a key.
            self.dataValuesPerInputState = {}
            sensors = []
            for key,val in cont.items():
                for name,sen in val[1]["raw_data_names"].items():
                    sensors.append(name)
                self.dataValuesPerInputState[key] = copy.deepcopy(sensors)
                del sensors[:]
                if not val[1]["raw_data_names"]:
                    self.dataValuesPerInputState[key] = key

            f.close()
        except IOError:
            print "Could not open JSON file"



    def startThreads(self):
        """Starts all threads, called in main"""
        self.consumerThread.start()
        self.incomingDataThread.start()
        self.stateUpdateThread.start()
        self.broadcastStateThread.start()

    def stopThreads(self):
        """stops all threads
        
        TODO:
            figure out how to kill threads more effectively and
            forgo the daemon status used to avoid script hanging
            on exit.
        """
        self.consumerThread.stop()
        self.incomingDataThread.stop()
        self.stateUpdateThread.stop()
        self.broadcastStateThread.stop()
        self.consumerThread.join()
        self.incomingDataThread.join()

    def setNextState(self):
        """Sets the next state if the transition logic is detected.
        
        This function begins by testing logic for the "all" key, which is 
        done prior to detecting a state transition based on current state.
        Transitions listed in the "all" section are preliminary for all states
        and so will be the more critical logic that detects a system failure,
        or logic that allows for transition to a custom state such as a manual
        override mode. Once the "all" conditions have been considered, the 
        function moves on the state transition logic by current state is evaluated
        if possible.

        Returns:
            True is the state has changed
        """
        try:
            ifAllCondition = self.validTransitions["all"]

            for goto in ifAllCondition:
                try:
                    currLogic = self.stateTransitionLogic["all+%s"%(goto)]
                except KeyError as e:
                    print "Invalid Transistion Request"
                    return

                if not currLogic:
                    result = 0
                else:
                    result = 1

                for key,val in currLogic.items():
                    if (self.inputLogicState[key] != val):
                    #if (self.inputLogicState[key] & val) == 0:
                        result = 0
                if result == 1 and self.currentState != goto:
                    self.currentState = goto
                    return True

        except KeyError:
            #consider logging here
            pass


        try:
            currConditions = self.validTransitions["%s"%self.currentState]
            for goto in currConditions:
                try:
                    currLogic = self.stateTransitionLogic["%s+%s"%(self.currentState,goto)]
                except KeyError as e:
                    print "Invalid Transistion Request"
                    return
                result = 1
                for key,val in currLogic.items():
                    if (self.inputLogicState[key] != val):
                    #if (self.inputLogicState[key] & val) == 0:
                        result = 0
                if result == 1 and self.currentState != goto:
                    self.currentState = goto
                    return True
        except KeyError:
            #consider logging here
            pass

        return False



    def setStateInputLogic(self, inputLogicName, dataName):
        """Takes the rawData and logic type and updates the input logic.

        Returns:
            True if the logic has changed.
        TODO:
            add support for logic other than range
        """
        if self.inputLogicType[inputLogicName] == "range":

            rangeTest = self.checkIfStateShouldChange(inputLogicName)

            if self.inputLogicState[inputLogicName] != rangeTest:
                self.inputLogicState[inputLogicName] = rangeTest
                return True
            else:
                return False

        if self.inputLogicType[inputLogicName] == "boolean":
            pass
        if self.inputLogicType[inputLogicName] == "boolean_XOR":
            pass




    def checkIfStateShouldChange(self, inputLogicName):
        """checks if atleast one of the current rawData entries is true

        Only returns 0 is all rawData entries per input logic are 0
        """
        result = 0
        for currentValue in self.dataValuesPerInputState[inputLogicName]:
            result = result | self.outOfRange(currentValue, self.inputLogicParams[inputLogicName])
        return result




    def outOfRange(self, sensorName, rangeParams):
        """Detects if reading is out of range"""
        data = self.rawData.dataCollectionByType[sensorName].retrieveMostCurrentEntry()
        if data == None:
            return 0
        if data > rangeParams[1] or data < rangeParams[0]:
            return 1
        else:
            return 0








if __name__ == "__main__":
    sensorData = zmq.Context()

    sensorDataSocket = sensorData.socket(zmq.SUB)

    sensorDataSocket.connect("tcp://192.168.10.2:5000")
    sensorDataSocket.setsockopt(zmq.SUBSCRIBE, '')
    
    #outsock_ctx = zmq.Context()
    outSock = sensorData.socket(zmq.PUB)
    outSock.bind("tcp://192.168.10.1:6000")

    master = stateMachineControl(1, "nextStateInfo.json", "stateInputLogic.json", sensorDataSocket, outSock)

    chipAddr = [0x69,0x6a,0x6b,0x6c]
    channelSelect = [0x80, 0xa0, 0xc0, 0xe0]
    for idx,chip in enumerate(chipAddr, 1):
        for ndx,chan in enumerate(channelSelect, 1):
            master.rawData.createNewEntry("PI_1_U%s_CH%s"%(idx, ndx))
    master.startThreads()

    #dataIn = incomingDataThread(master.rawData, master.inputLogicQueue, sensorDataSocket)
    #dataConsumer = dataConsumerThread(master, master.inputLogicQueue)
    exitFlag = 0
    while True:
        exitFlag = input()
        if exitFlag == 1:
            master.stopThreads()
            sys.exit()
