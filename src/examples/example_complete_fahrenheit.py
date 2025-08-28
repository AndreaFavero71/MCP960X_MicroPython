"""
Example code to use the mcp_960x.py library

"""

from machine import Pin, SoftI2C
from mcp960x import MCP960X
import time, sys


# hardware setup for the MCP960X alert pins (up to 4)
ALERT1 = Pin(1, Pin.IN)                  # pin for the MCP960X alert1
ALERT2 = Pin(2, Pin.IN)                  # pin for the MCP960X alert2

# float coefficient value for degrees Celsius to Fahrenheit conversion
C_TO_F_COEFF = 9/5                       # fractional coefficient from Celsius to Fahrenheit

# float coefficient value for degrees Fahrenheit to Celsius conversion
F_TO_C_COEFF = 5/9                       # fractional coefficient from Fahrenheit to Celsius

# define the temperature to activate the alert 1 (acts also on GPIO)
# active when raising above, resetting when lowering below ALERT1_TEMP_F - ALERT1_HYST_F
ALERT1_TEMP_F = 500                      # F temperature for the alert1
ALERT1_HYST_F = 50                       # F temp hysteresys to reset alert1                     
alert1_active = False                    # flag monitoring the alert1

# define the temperature to activate the alert 2 (acts also on GPIO)
# active when raising above, resetting when lowering below ALERT2_TEMP_F - ALERT2_HYST_F
ALERT2_TEMP_F = 1000                     # F temperature for the alert2
ALERT2_HYST_F = 100                      # F temp hysteresys to reset alert2
alert2_active = False                    # flag monitoring the alert2



def c_to_f(temp_c):
    """Function to convert Celsius to Fahrenheit"""
    return temp_c * C_TO_F_COEFF + 32


def f_to_c(temp_f):
    """Function to convert Fahrenheit to Celsius"""
    return (temp_f - 32) * F_TO_C_COEFF


def read_c_temp():
    """
    Reads the hot-junction temperature from the MCP960X module.
    Returns temperature in Celsius
    """
    return tc.read_temperatures()['T_H']


def read_f_temp():
    """
    Reads the hot-junction temperature from the MCP960X module (in Celsius).
    Returns temperature in Fahrenheit.
    """
    return c_to_f(read_c_temp())   

    
def alert_1_handler(pin):
    "Callback GPIO interrupt on ALERT1 pin"
    global alert1_active
    if ALERT1.value():
        alert1_active = True
    else:
        alert1_active = False


def alert_2_handler(pin):
    "Callback GPIO interrupt on ALERT2 pin"
    global alert2_active
    if ALERT2.value():
        alert2_active = True
    else:
        alert2_active = False


# Sodt I2C serial communication, initialized first at low I2C frequency
soft_i2c = SoftI2C(scl=Pin(15), sda=Pin(14), freq=20_000)
time.sleep(0.5)  # delay time after setting the soft I2C


# check I2C devices (SoftI2C at low I2C frequency, preventing MCP960X to mess up)
i2c_devices = soft_i2c.scan()


# Soft I2C serial communication, at higher I2C frequency (do not i2c.scan() at this frequency)
soft_i2c = SoftI2C(scl=Pin(15), sda=Pin(14), freq=120_000)
time.sleep(0.5)  # delay time after setting the soft I2C


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


# set the alert1 to MCP960X
rising = True if f_to_c(ALERT1_TEMP_F) > 0 else False
limit = int(f_to_c(ALERT1_TEMP_F))
hysteresis = min(0, int(F_TO_C_COEFF * ALERT1_HYST_F))
tc.set_alert(alert_num = 1,
             limit = limit,
             hysteresis = hysteresis,
             rising = rising)
time.sleep_ms(20)


# set the alert2 to MCP960X
rising = True if f_to_c(ALERT2_TEMP_F) > 0 else False
limit = int(f_to_c(ALERT2_TEMP_F))
hysteresis = min(0, int(F_TO_C_COEFF * ALERT2_HYST_F))
tc.set_alert(alert_num = 2,
             limit = limit,
             hysteresis = hysteresis,
             rising = rising)
time.sleep_ms(20)


# set interrupt on ALERT1 pin
ALERT1.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=alert_1_handler)

# set interrupt on ALERT2 pin
ALERT2.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=alert_2_handler)


# check the MCP960X status
print("\nStatus:")
mcp_status = tc.get_status()
for parameter, status in mcp_status.items():
    print(f"   {parameter} = {status}")
print()



while True:
    temp_f = read_f_temp()
    print(f"Temperature (Fahrenheit) = {temp_f:.1f}  |  alert1: {alert1_active}  |  alert2: {alert2_active}")
    time.sleep_ms(1000)
    

