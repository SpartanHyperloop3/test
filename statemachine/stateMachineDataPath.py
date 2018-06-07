import zmq
import time
import threading
import copy
import sys
import json
import RPi.GPIO as GPIO
import smbus
import Queue
import dataController


class stateMachineDataPath(object):
    """Sets the outputs based on state and reports feedback.


    """
    class incomingDataThread(threading.Thread):
        """Retrieves incoming data from master.

        Creates a thread object that collects data from the master
        controller. Data should be sent as a list with the first object
        being a string identifying the type of data sent ["data_type", data].
        State data is denoted by string "state", and upon recieving state data
        an event in outer class stateMachineDataPath (currentStateHasChanged)
        is set to notify the outputsThread that the states has changed.
        """
        def __init__(self, control, zmqSock):
            """incomingDataThread constructor.

            Initializes dataThread

            Args:
                control: must pass outer class object to obtain access to methods.
                zmqSock: current socket for incoming data
            """
            threading.Thread.__init__(self)
            self.name = "incoming_data"
            self._killFlagIn = threading.Event()
            self.control = control
            self.sock = zmqSock
            self.poller = zmq.Poller()
            self.poller.register(self.sock, zmq.POLLIN)

        def run(self):
            while not self._killFlagIn.is_set():
                if self.poller.poll(1000):
                    message = self.sock.recv_json()
                    if message[0] == "state":
                        self.control.currentState = message[1]
                        self.control.currentStateHasChanged.set()

        def stop(self):
            self._killFlagIn.set()


    class outputsThread(threading.Thread):
        """Controls setting outputs on state updates

        Waits fro currentStateHasChanged event to be set then sets outputs
        according to the state.
        """
        def __init__(self, control):
            threading.Thread.__init__(self)
            self._killFlagOut = threading.Event()
            self.control = control
            self.name = "output_control"

        def run(self):
            while not self._killFlagOut.is_set():
                if self.control.currentStateHasChanged.wait(5.0):
                    self.control.currentStateHasChanged.clear()
                    self.control.setOutputsByState()

        def stop(self):
            self._killFlagOut.set()


    class ADCconsumer(threading.Thread):
        """Gets readings from the ADCs.

        Takes a request for a reading from a queue which holds the chip
        address and channel to read from and sends the data to the master.
        """
        def __init__(self, control, ADCqueue):
            threading.Thread.__init__(self)
            self.name = "ADC_consumer_thread"
            self._killFlag = threading.Event()
            self.control = control
            self.queue = ADCqueue
            self.reading = []


        def run(self):
            while not self._killFlag.is_set():
                try:
                    nextJob = self.queue.get(True, 2.0)
                    #print nextJob[0], nextJob[1], nextJob[2]
                except Queue.Empty:
                    pass
                else:
                    self.updateAndSendADCreading(nextJob[0], nextJob[1], nextJob[2])


        def stop(self):
            self._killFlag.set()


        def getADCreading(self, chipAddr, channel, name):
            bus = smbus.SMBus(1)
            result = bus.read_i2c_block_data(chipAddr,channel)
            time.sleep(.001)
            result = bus.read_i2c_block_data(chipAddr,channel)
            upper = (result[0] & 15)
            upper = (upper << 8)
            total = upper + result[1]
            voltage = float(total * .001)
            self.reading = [name, voltage, time.time()]


        def updateAndSendADCreading(self, chipAddr, channel, name):
            self.getADCreading(chipAddr, channel, name)
            with globalLock:
                self.control.sendData(self.reading)





    class ADCthread (threading.Thread):
        """Creates requests for an ADC reading
        
        A thread is created for each channel on a chip that requires a reading.
        The threads continuously add to a queue a request for a reading. The 
        request is a list that includes the sensor name, chip address, and channel.
        """

        def __init__(self, control, name, samplingPeriod, chipAddr, channel, ADCqueue):
            threading.Thread.__init__(self)
            self.name = name
            self.samplingPeriod = samplingPeriod
            self._killFlagADC = threading.Event()
            self.channel = channel
            self.chipAddr = chipAddr
            self.control = control
            self.queue = ADCqueue
            self.daemon = True


        def run(self):
            while not self._killFlagADC.is_set():
                self.queue.put([self.chipAddr, self.channel, self.name])
                time.sleep(self.samplingPeriod)


        def stop(self):
            self._killFlagADC.set()











    def __init__(self, setInitialState = 0, stateOutputsJSONfile = None, sensorInitializationJSONfile = None, incomingSocket = None, outgoingSocket = None):
        """stateMachineDataPath constructor.

        Args:
            setInitialState: sets the initial stat attribute.
            stateOutputsJSONfile: contains information on outputs for each state.
            sensorInitializationJSONfile: contains information about which ADC channels
            and GPIO pins will be used for sensor readings and inputs.
            incomingSocket: incoming data socket.
            outgoingSocket: outgoind data socket.
        """

        GPIO.setmode(GPIO.BCM)

        self.currentState = setInitialState
        self.currentStateHasChanged = threading.Event()
        self.incomingSocket = incomingSocket
        self.outgoingSocket = outgoingSocket
        self.ADCthreads = []
        self.ADCqueue = Queue.Queue()
        self.ADCconsumerThread = self.ADCconsumer(self, self.ADCqueue)

        self.incomingDataThread = self.incomingDataThread(self, self.incomingSocket)
        self.outputsThread = self.outputsThread(self)
        self.lock = threading.Lock()


        #output JSON file parsing starts here
        try:
            f = open(stateOutputsJSONfile, "r")
            outputJSON = json.loads(f.read())
            self.outputsGPIObyState = {}
            for key,val in outputJSON.items():
                self.outputsGPIObyState[key] = val["GPIO"]

            self.outputFunctionsByState = {}
            for key,val in outputJSON.items():
                self.outputFunctionsByState[key] = val["function"]

            self.outputsGPIO = []
            for key,val in outputJSON.items():
                for pin in val["GPIO"]:
                    if pin[0] not in self.outputsGPIO:
                        self.outputsGPIO.append(pin[0])

        except (IOError, TypeError):
            print "Could not open state output JSON file: %s" % stateOutputsJSONfile


        #input JSON file parsing starts here
        try:
            f = open(sensorInitializationJSONfile, "r")
            inputsfile = json.loads(f.read())


            self.analogSensors = {}
            for key,val in inputsfile.items():
                if val["type"] == "analog":
                    self.analogSensors[key] = { "sample_rate" : val["sample_rate"], "location" : val["location"] }


            self.digitalInputs = {}
            for key,val in inputsfile.items():
                if val["type"] == "digital":
                    self.digitalInputs[key] = { "location" : val["location"], "PUD" : val["PUD"]}


        except (IOError, TypeError):
            print "Could not open sensor and input JSON file: %s" % sensorInitializationJSONfile



    def setOutputsByState(self):
        """sets the outputs on state change

        When the state is changed this function is called to change outputs
        by state.
        """
        try:
            for output in self.outputsGPIObyState["%s"%self.currentState]:
                self.writeGPIOoutput(output[0], output[1])
                print "Current state of pin %s is: %s\n"%(output[0],GPIO.input(output[0]))

            for func in self.outputFunctionsByState["%s"%self.currentState]:
                self.startFunc(func["name"], func["arguments"])

        except KeyError:
            print "No state in JSON file"



    def initializeInputsAndSensors(self):
        """Initializes inputs and sensors"""

        for key,val in self.analogSensors.items():
            t = self.ADCthread(self, key, val["sample_rate"], val["location"][0], val["location"][1], self.ADCqueue)
            self.ADCthreads.append(t)

        for key,val in self.digitalInputs.items():
            GPIO.setup(val["location"], GPIO.IN, pull_up_down=getattr(GPIO, val["PUD"]) )
            GPIO.add_event_detect(val["location"], GPIO.RISING, bouncetime=200)
            cb = lambda channel, arg1 = key, arg2 = 1:self.GPIOevent(arg1, arg2)
            GPIO.add_event_callback(val["location"], cb)



    def initializeOutputs(self):
        """Initializes outputs"""
        for output in self.outputsGPIO:
            GPIO.setup(output, GPIO.OUT)



    def startThreads(self):
        self.incomingDataThread.start()
        self.outputsThread.start()
        self.ADCconsumerThread.start()
        for thread in self.ADCthreads:
            thread.start()



    def stopThreads(self):
        print "Killing ADC consumer thread.."
        #for t in self.ADCthreads:
        #    print threading.active_count()
        #    print t.getName()
        #    t.stop()
        #    t.join()
        #    print "done.."
        print "done.."
        self.ADCconsumerThread.stop()
        self.ADCconsumerThread.join()
        print "Killing output thread.."
        self.outputsThread.stop()
        self.outputsThread.join()
        print "done.."
        print "killng incoming data thread.."
        self.incomingDataThread.stop()
        self.incomingDataThread.join()
        print "done..goodbye"



    def setGPIOlistener(self, pin):
        pass



    def writeGPIOoutput(self, pin, state):
        """Writes to a pin if it is not an input"""
        if not self.isGPIOinput(pin):
            GPIO.output(pin, state)
        else:
            print "GPIO pin %s is an input"%pin



    def printState(self, *args):
        """Test func"""
        print "The current state is: %s"%self.currentState
        print "arguments passed to func: %s"%args



    def accelerationSetPoint(self, input1, input2):
        """Test func"""
        print "Setting Acceleration"



    def startFunc(self, name, args):
        """Starts a function"""
        getattr(self, name)(*args)



    def GPIOevent(self, arg1, arg2):
        """Called when a GPIO event occurs.
        
        Args:
            arg1: sensor or input name.
            arg2: sensor or input reading.
        """
        self.sendData([arg1,arg2,time.time()])



    def sendData(self, data):
        self.outgoingSocket.send_json(data)



    def isGPIOinput(self, pin):
        """Determines if a pin is an input
        
        Args:
            pin: the pin to check.

        Returns:
            True if the pin is set as an input.
        """
        result = False
        try:
            for key in self.digitalInputs.keys():
                if pin == self.digitalInputs[key]["location"]:
                    result = True
        except KeyError:
            print "key error"
        return result
    def __enter__(self):
        return self




if __name__ == "__main__":
    exitFlag = 0
    context = zmq.Context()
    outsock = context.socket(zmq.PUB)
    outsock.bind("tcp://*:5000")

    insock = context.socket(zmq.SUB)
    insock.setsockopt(zmq.SUBSCRIBE, '')
    insock.connect("tcp://%s:6000"%sys.argv[1])

    dataPath = stateMachineDataPath(1, "PI_1_Outputs.json", "PI_1_Sensors.json", insock, outsock)

    globalLock = threading.Lock()
    dataPath.initializeInputsAndSensors()
    dataPath.initializeOutputs()
    dataPath.startThreads()

    while True:
        try:
            exitFlag = input()
            if exitFlag == 1:
                print "Stopping Threads.."
                dataPath.stopThreads()
                GPIO.cleanup()
                sys.exit()
        except (SyntaxError, NameError):
            pass
