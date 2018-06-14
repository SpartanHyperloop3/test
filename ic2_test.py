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
-max frequency is 100 kHz and min is 10 kHz
'''

#default i2c address
DEVICE_ADDRESS = 0x5A

#command masks
COMMAND_RAM_ACCESS_MASK = 0b00000000
COMMAND_EEPROM_ACCESS_MASK = 0b00100000
COMMAND_READ_FLAGS = 0b11110000

#RAM addresses
DATA_IR_CHANNEL_1 = 0x04
T_OBJ1 = 0x07 # object temp Toreg * 0.02 = temp in kelvin | MSB is an error flag (it should be 0)

#EEPROM addresses
SMBUS_ADDRESS = 0x0E
EMISSIVITY_ADDRESS = 0x04
TA_ADDRESS = 0x06 #ambient temp Tareg * 0.02 = temp in kelvin

#emissivity
PAPER_EMISSIVITY = 0.68
device_emissivity = hex(int(round(65535 * PAPER_EMISSIVITY)))

#command choice
desired_command = COMMAND_RAM_ACCESS_MASK | T_OBJ1

bus = smbus.SMBus(1)

#change emissivity
#write 0
#write actual

#figure out how to have multiple temp sensors on one i2c bus (page 14)

#read in temp value
while (True):
    result = bus.read_word_data(DEVICE_ADDRESS, desired_command)
    #print(bin(result))
    #print(hex(result))
    #print(result)
    print(result * 0.02 - 273.15)
    time.sleep(1)
