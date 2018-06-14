from tkinter import Tk, Label, Button

class ControlButtonGUI:
    def __init__(self, master):
        self.master = master
        master.title("A simple GUI")

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
        print("Send state 1")


    def test_actuators(self):
        print("Send state 14")

    def enter_track(self):
        print("Send state 2")

    def exit_track(self):
        print("Send state 10")

    def shutdown(self):
        print("Send state 11")

    def wait(self):
        print("Send state 17")

    def manual_operation(self):
        print("Send state 54")

    def emergency(self):
        print("Send state 13")

root = Tk()
my_gui = ControlButtonGUI(root)
root.mainloop()