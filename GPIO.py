import RPi.GPIO as GPIO

def GPIO_stuff():
    GPIO.setmode(GPIO.BOARD)
    print(GPIO.getmode())
    testpin = 13
    GPIO.setup(testpin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    print(GPIO.input(testpin))
    GPIO.cleanup()

GPIO_stuff()