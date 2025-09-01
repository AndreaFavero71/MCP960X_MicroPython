# MCP960X MicroPython Library
A MicroPython library for the MCP9600 and MCP9601 thermocouple amplifiers, communicating via the I2C bus.
<br><br><br>

## Motivations for this library
While experimenting with existing MicroPython libraries, I encountered several issues.<br>
After spending considerable time cross-checking the MCP960X datasheet to resolve these issues, I decided it would be more effective to develop a new library from scratch.<br>
*Note: it’s also possible that I didn’t use the existing libraries correctly.*
<br><br><br>

## Common boards using MCP9600 or MCP9601
Among other boards, the MCP9600 and MCP9601 chips are used on the following Adafruit boards:
![title image](/pictures/mcp9600_mcp9601.jpg)<br>
<small>Product images courtesy of [Adafruit](https://www.adafruit.com)</small>
<br><br><br>

## MCP960X main characteristics
* Supports Type K, J, T, N, S, E, B, and R thermocouples.
* All temperatures (settings and readings) are in Celsius.
* Returns the Hot-junction temperature, Cold-junction temperature (the chip temperature), and their difference (delta).
* Includes a configurable IIR digital filter to smooth temperature fluctuations.
* Features 4 configurable alarms that can be monitored via I2C or the dedicated A1-A4 output pins.
* The MCP9601 is a more feature-rich version of the MCP9600, offering improved fault detection capability.<br>

Check the Microchip [datasheet](docs/Microchip/MCP960X-L0X-RL0X-DS20005426.pdf) for more information.
<br><br><br>

## Installation
1. The library consists of a single MicroPython file: `mcp960x.py`.
2. Copy the `mcp960x.py` file to your MicroPython device's filesystem (e.g., the root folder or the `/lib` folder).
3. Wire your MCP960X board to your microcontroller.
4. Ensure you have 4.7kΩ pull-up resistors on the SCL and SDA I2C lines.
<br><br><br>

## Usage
1. Import the necessary libraries from `machine`.
2. Import the `MCP960X` library.
3. Initialize the I2C bus.
4. Instantiate the thermocouple amplifier object.
5. Check if the MCP960X module is detected in the I2C bus.
7. Read the temperatures. The library returns a dictionary with Hot-junction, Cold-junction and delta temperature.
```
from machine import Pin, SoftI2C
from mcp960x import MCP960X

scl_pin = 5                                                      # I2C-compatible SCL pin
sda_pin = 4                                                      # I2C-compatible SDA pin
i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=20_000)   # initialize I2C bus
tc = MCP960X(i2c)                                                # instantiate TC (default = type K thermocouple)

if 0x67 not in i2c.scan():                                       # device detection check (default address = 0x67)
    raise ValueError("MCP960X not found at address 0x67. Check wiring, pull-up resistors, and address.")

temps = tc.read_temperatures()                                   # reads temperatures in °C
temp_c = temps['T_H']                                            # Hot-junction temp in °C
print(f"temp_c: {temp_c}")                                       # print temperature (°C) to the Shell / terminal

# temp_cj = temps['T_C']                                         # Cold-junction temp in °C
# temp_delta = temps['T_delta']                                  # delta temp Hot-junction - Cold-junction (°C)

# temp_f = 32 + (9/5) * temps['T_H']                             # Hot-junction temp in °F
```
<br>

## TC configuration options
```
tc = MCP960X(i2c,                         # initialized I2C bus
             address=0x67,                # I2C address         (can be changed via hardware)
             tctype='K',                  # thermocouple type: 'K','J','T','N','S','E','B','R' (default: 'K')
             tcfilter=4,                  # IIR filter: 0 - 7  (4 = medium, averages 32 samples)
             cold_junction_res = 0.0625,  # 0.0625 or 0.25     (lower = higher resolution and higher Hot-junction accuracy)
             adc_resolution = 18)         # ADC resolution: 12,14,16,18 bits (higher resolutions = slower)
```
<br><br>

## Quick test
A quick test is provided in the `minimal_example.py` file.<br>
Type `import minimal_example` on the REPL/IDE shell to print the temperature (°C) every second.
```
>>> import minimal_example

MCP9600: Device ID = 0x40, Revision = 0x14

Temperature (Celsius) = 23.9
Temperature (Celsius) = 23.9
Temperature (Celsius) = 23.9
Temperature (Celsius) = 23.9
Temperature (Celsius) = 23.9
Temperature (Celsius) = 23.9
```
<br><br>

## Examples
The [examples](src/examples/) folder contains more detailed usage examples, including how to configure and use the alarm functions.
<br><br><br>

## I2C notes and workarounds
Based on practical experience:
1. The library works more reliably with `SoftI2C` than with the hardware `I2C` peripheral.
2. If `i2c.scan()` does not detect the device, try initializing the I2C bus at a lower frequency (e.g., up to 30 kHz). After a successful scan, you can increase the frequency (e.g. up to 120KHz).
3. I2C frequencies above approximately 160 kHz may cause communication issues.
<br><br><br>

## Tested on
* **Board:** RP2040-Zero
* **MicroPython version:** v.1.24.1
* **Hardware:** MCP9600 board from Adafruit, modified for thermocouple Open-circuit detection. Also tested the Adafruit MCP9601, by a friend of mine (thank you Séan).
<br><br><br>

## Modified MCP9600 for TC open-circuit detection
The Adafruit MCP9600 board does not include the circuitry required for thermocouple open-circuit detection.<br>
This can be added by installing three resistors, as recommended by Microchip:
![title image](/pictures/mcp9600_OC_detection.jpg)<br>
<small>Diagrams extracted from the Microchip MCP960X datasheet.</small>
<br><br><br>

## Library reference
The Library is based on the Microchip [datasheet DS20005426](docs/Microchip/MCP960X-L0X-RL0X-DS20005426.pdf) dated 09/14/21.
<br><br><br>

## Other documents
Other relevant documents from Microchip and Adafruit can be found in the [docs](docs/) folder.
<br><br><br>

## Feedback & contributing
Found a bug, have a suggestion for an improvement, or want to share your project using this library? Your feedback is welcome!<br>
Open an [Issue](https://github.com/AndreaFavero71/MCP960X_MicroPython/issues) on GitHub to report bugs.<br>
Submit a [Pull Request](https://github.com/AndreaFavero71/MCP960X_MicroPython/pulls) directly if you'd like to contribute code.
<br><br><br>

## License
This project is licensed under the MIT License: You are free to use, modify, and distribute it, provided that the license text is included in copies or substantial portions of the software.
<br><br><br>
   
