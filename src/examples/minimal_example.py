"""
Minimal example code to use the mcp_960x.py library

"""

from machine import Pin, SoftI2C
from mcp960x import MCP960X
import time, sys


def read_temp():
    """
    Reads the hot-junction temperature from the MCP960X module.
    Returns temperature in Celsius
    """
    return tc.read_temperatures()['T_H']


# Sodt I2C serial communication
soft_i2c = SoftI2C(scl=Pin(15), sda=Pin(14), freq=20_000)
time.sleep(0.5)  # delay time after setting the soft I2C


# check I2C devices (SoftI2C at low I2C frequency, preventing MCP960X to mess up)
i2c_devices = soft_i2c.scan()


# thermocouple object
tc = MCP960X(soft_i2c, address=0x67,
             tctype="K",
             tcfilter=4,                  # (0 to 7) 4 is a medium filter, taking ca 32 readings into account
             cold_junction_res = 0.0625,  # (0.0625 or 0.25) lower value, higher resolution, higher Hot Junction accuracy 
             adc_resolution = 18)         # (12,14,16,18 bits) higher resolution lower speed, yet same Hot Junction accuracy


# check if the MCP960X module is detected by the I2C bus
time.sleep(0.5)
if len(i2c_devices) == 0:
    print("No i2c device !")
    sys.exit(0)


# checks which MCP module is connected, MCP960X (ID = 0x40) or MCP9601 (ID = 0x41)
mcp906x_ID = tc.dev_id                    # MCP ID is assigned to mcp906x_ID


while True:
    temp_c = read_temp()
    print(f"Temperature (Celsius) = {temp_c:.1f}")
    time.sleep_ms(1000)
    
