"""change send_json format, 
check if while loop is needed for continuous sending of json
"""




from tkinter import Tk, Label, Button
import sys
import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://127.0.0.1:2000')


class ControlButtonGUI:
    def __init__(self, master):
        self.master = master
        master.title("Off-pod Control System")

        self.label = Label(master, text="This is a Control button GUI!")
        self.label.pack()

        self.stateone_button = Button(master, text="1) Initialise and test sensors", command=self.test_sensors, bg="yellow")
        self.stateone_button.pack()

        self.statefourteen_button = Button(master, text="14) Initialise and test actuators", command=self.test_actuators, bg="blue")
        self.statefourteen_button.pack()

        self.statetwo_button = Button(master, text="2) Enter track", command=self.enter_track, bg="green")
        self.statetwo_button.pack()

        self.stateten_button = Button(master, text="10) Exit track", command=self.exit_track, bg="cyan")
        self.stateten_button.pack()

        self.stateeleven_button = Button(master, text="11) Shutdown", command=self.shutdown, bg="magenta")
        self.stateeleven_button.pack()

        self.stateseventeen_button = Button(master, text="17) Waiting", command=self.wait)
        self.stateseventeen_button.pack()

        self.statefiftyfour_button = Button(master, text="54) Manual operation mode", command=self.manual_operation, bg="yellow")
        self.statefiftyfour_button.pack()


        self.statethirteen_button = Button(master, text = "13) Emergency shutdown", command=self.emergency, bg = "red")
        self.statethirteen_button.pack()

        self.close_button = Button(master, text = "Close the window", command=master.quit)
        self.close_button.pack()


    def test_sensors(self):
        print("Sending state 1")
        socket.send_json(["PC": {
        "reading": 1,
        "time": null,
        "units": "PC"
        }])               


    def test_actuators(self):
        print("Sending state 14")
        socket.send_json(["PC": {
        "reading": 14,
        "time": null,
        "units": "PC"
        }])                        #another json for master, or change the format here

    def enter_track(self):
        print("Sending state 2")
        socket.send_json(["PC": {
        "reading": 2,
        "time": null,
        "units": "PC"
        }])

    def exit_track(self):
        print("Sending state 10")
        socket.send_json(["PC": {
        "reading": 10,
        "time": null,
        "units": "PC"
        }])

    def shutdown(self):
        print("Sendinng state 11")
        socket.send_json(["PC": {
        "reading": 11,
        "time": null,
        "units": "PC"
        }])

    def wait(self):
        print("Sending state 17")
        socket.send_json(["PC": {
        "reading": 17,
        "time": null,
        "units": "PC"
        }])

    def manual_operation(self):
        print("Sending state 54")
        socket.send_json(["PC": {
        "reading": 54,
        "time": null,
        "units": "PC"
        }])

    def emergency(self):
        print("Sending state 13")
        socket.send_json(["PC": {
        "reading": 13,
        "time": null,
        "units": "PC"
        }])

root = Tk()
my_gui = ControlButtonGUI(root)
root.mainloop()
