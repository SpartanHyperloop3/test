from array import array
import RPi.GPIO as GPIO

pi_pin = array(20)                                          # For however many local sensors; this sample uses 20

GPIO.setmode(GPIO.BOARD)

for x, y in GPIO(20):                                       # Pin Initialization
    if y == "OUT":                                          # Example of 2 output pins
        GPIO.setup(x, GPIO.y, pull_up_down=GPIO.PUD_DOWN)   # Output active operating @ 3.3V
        GPIO.output(x)
    if y == "IN":
        GPIO.setup(x, GPIO.y)
        GPIO.input(x, GPIO.HIGH)                            # Input active operating @ 3.3V

def data_in_out():
    for q in GPIO(20):
        if y == "IN":                                       # If we have a pin that is an active input
            GPIO.output(p) = "actuator_input"
            q += 1                                          # Increment q past pin for we dont need to send it's data
        else
            pi_pin[q] = GPIO(q)                             # Store GPIO values to array and send to global storage
    return pi_pin[20]

def globalstorage():
    data_in_out()
    return
