import smbus
import time

'''
MLX90614 Thermometer
-Only read_word_data and write_word_data are supported by MLX90614 thermometers
-EEPROM locations:
--Emissivity = dec2hex[round(65535 x physical emissivity value) value = 0.1...1.0
---address 0x04
---must erase (write 0) before writing desired data
--SMBus address (LSByte only) 0x0E
--config register 1 address 0x05
-RAM locations:
--raw data IR channel 1: 0x04
--raw data IR channel 2: 0x05
--Ta: 0x06
--Tobj1: 0x07
--Tobj2: 0x08
-bottom of page 14 discusses changing i2c address (for if we have multiple thermometers on a single bus)
'''

DEVICE_ADDRESS = 0x5A
COMMAND_RAM_ACCESS_MASK = 0b00000000
COMMAND_EEPROM_ACCESS_MASK = 0b00100000
COMMAND_READ_FLAGS = 0b11110000

DATA_IR_CHANNEL_1 = 0x04
T_OBJ1 = 0x07

desired_command = COMMAND_RAM_ACCESS_MASK | T_OBJ1

bus = smbus.SMBus(1)
result = bus.read_word_data(DEVICE_ADDRESS, desired_command)
while(True):
    print(result)
    time.sleep(1)