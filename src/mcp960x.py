"""
Andrea Favero 26/08/2025      rev 0.1

Micropython library for MCP9600 and MCP9601 thermocouple amplifier (I2C bus)

This library is based on microchip datasheet 'DS20005426.pdf' dated 09/14/21
Along the code the are some reference to chapters and pages of the datasheet.

Tested on MCP9600 and by a friend on MCP9061 (Adafruit boards)
Tested with RP2040-Zero and type K Termocouple
Used 4k7 pullup resistors on I2C


Notes:
  Most of Registers return 1 byte, others 2 bytes and 1 case of 3 bytes.
      
  When reading a Register having > 1 byte info, there is no need to
  resend the Register or increase the pointer; The MCP960X increment
  the pointer automatically. It took me some hours to learn it...




MIT License

Copyright (c) 2025 Andrea Favero

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

from time import sleep_us
import struct


class MCP960X:
    # register addresses
    REG_HOT_JUNCTION     = 0x00
    REG_DELTA_TEMP       = 0x01
    REG_COLD_JUNCTION    = 0x02
    REG_RAW_ADC          = 0x03
    REG_STATUS           = 0x04
    REG_THERMO_CONFIG    = 0x05
    REG_DEVICE_CONFIG    = 0x06
    REG_ALERT_STATUS     = 0x07
    REG_ALERT_CONFIG     = 0x08  # base for alert configs (4 registers: 0x08-0x0B)
    REG_ALERT_HYSTERESIS = 0x0C  # base for hysteresis (4 registers: 0x0C-0x0F)
    REG_ALERT_LIMIT      = 0x10  # base for limits (4 registers, 2 bytes each: 0x10-0x13)
    REG_DEVICE_ID        = 0x20
    
    # resolutions for the Hot Junction reading
    ADC_RESOLUTIONS = {12: 0b11,
                       14: 0b10,
                       16: 0b01,
                       18: 0b00  # default setting
                       }
    
    # resolution for the Cold Junction
    COLD_JUNCTION_RES = {0.0625: 0b0,  # default (higher precision)
                         0.25:   0b1   # lower precision (higher speed)
                         }
    
    
    def __init__(self, i2c, address=0x67, tctype="K", tcfilter=0,
                 cold_junction_res = 0.0625, adc_resolution = 18):
        
        self.i2c = i2c
        self.address = address
        self._t_stretch = 60                        # µs (clock stretching delay 60us, p.9)
        self._adc_resolution = adc_resolution       # set the ADC resolution (default = 18 bits)
        self._cold_junction_res = cold_junction_res # set the cold junction resolution (default = 0.0625 degC)
        sleep_us(100000)
        
        self.dev_id, rev = self.get_device_id_and_revision()
        if self.dev_id == 0x40:
            print("\nMCP9600: Device ID = 0x{:02X}, Revision = 0x{:02X}".format(self.dev_id, rev), "\n")
        elif self.dev_id == 0x41:
            print("\nMCP9601: Device ID = 0x{:02X}, Revision = 0x{:02X}".format(self.dev_id, rev), "\n")
        else:
            print("Device ID differs from the known '0x40' (MCP9600) and '0x41' (MCP9601)")
        sleep_us(5000)
        
        self.set_thermocouple_type(tctype)     # set the TC type
        sleep_us(5000)
        
        self.set_filter_coefficient(tcfilter)  # set the IIR filter
        sleep_us(5000)
        
        self.set_resolution()                  # set default resolution
        sleep_us(5000)

    
    def _write_pointer(self, pointer):
        """Set register pointer for sequential reads."""
        self.i2c.writeto(self.address, bytes([pointer]))

    
    def _read_bytes(self, n_bytes):
        """Read `n_bytes` with clock stretching"""
        data = bytearray(n_bytes)
        self.i2c.readfrom_into(self.address, data)
        sleep_us(self._t_stretch)  # handle i2c t_STRETCH (p.9)
        return data
    
    
    def get_device_id_and_revision(self):
        self._write_pointer(self.REG_DEVICE_ID)
        data = self._read_bytes(2)
        return data[0], data[1]
    
    
    THERMOCOUPLE_TYPES = {
        'K': 0b000, 'J': 0b001, 'T': 0b010, 'N': 0b011,
        'S': 0b100, 'E': 0b101, 'B': 0b110, 'R': 0b111
    }

    
    def set_thermocouple_type(self, type_char):
        """Set thermocouple type (K/J/T/N/S/E/B/R)."""
        config = self._read_bytes(1)[0] & 0b10001111
        config |= (self.THERMOCOUPLE_TYPES[type_char.upper()] << 4)
        self.i2c.writeto(self.address, bytes([self.REG_THERMO_CONFIG, config]))

    
    def set_filter_coefficient(self, n=4):
        """Set digital filter coefficient (0=off, 7=max, p.35)."""
        config = self._read_bytes(1)[0] & 0b11111000
        config |= min(n, 7)
        self.i2c.writeto(self.address, bytes([self.REG_THERMO_CONFIG, config]))

    
    def read_temperatures(self):
        """Sequentially read T_H, T_delta, T_C (Reg 0x00-0x02)."""
        # get correct LSB based on resolution (Table 3-1 in datasheet)
        adc_lsb = {12: 1.0, 14: 0.25, 16: 0.0625, 18: 0.0625}.get(self._adc_resolution, 0.0625)
        cold_lsb = self._cold_junction_res  # already set to 0.0625 or 0.25
        self._write_pointer(self.REG_HOT_JUNCTION)
        data = self._read_bytes(6)  # 2 bytes per register
        temps = []
        for i in range(0, 6, 2):
            val = (data[i] << 8) | data[i+1]
            if val & 0x8000:  # negative temp
                val -= 65536
            # use adc_lsb for T_H and T_delta, cold_lsb for T_C
            lsb = cold_lsb if i == 4 else adc_lsb  # T_C is the 3rd value (bytes 4-5)
            temps.append(val * lsb)
        return {'T_H': temps[0], 'T_delta': temps[1], 'T_C': temps[2]}

    
    def set_resolution(self, adc_bits=18, cold_junction_res=0.0625):
        """Set ADC (12/14/16/18-bit) and cold junction resolution (0.0625/0.25°C)."""
        # validate ADC resolution
        if adc_bits not in self.ADC_RESOLUTIONS:
            adc_bits = 18  # Default to 18-bit
        self._adc_resolution = adc_bits
        
        # validate cold junction resolution (fallback to 0.0625 if invalid)
        if cold_junction_res not in self.COLD_JUNCTION_RES:
            cold_junction_res = 0.0625
        self._cold_junction_res = cold_junction_res
        
        # build config byte
        config = 0
        config |= self.ADC_RESOLUTIONS[adc_bits] << 5             # ADC resolution bits (5-6)
        config |= self.COLD_JUNCTION_RES[cold_junction_res] << 7  # Cold Junction res (bit 7)
    
        self.i2c.writeto(self.address, bytes([self.REG_DEVICE_CONFIG, config]))

    
    def set_power_mode(self, mode='normal'):
        """Set power mode: 'normal', 'shutdown', or 'burst'."""
        config = self._read_bytes(1)[0] & 0b11111100
        if mode == 'shutdown':   config |= 0b01
        elif mode == 'burst':    config |= 0b10
        self.i2c.writeto(self.address, bytes([self.REG_DEVICE_CONFIG, config]))

    
    def read_all_alerts(self):
        """Sequentially read Alert Configs, Limits, and Hysteresis."""
        # read Configs (Reg 0x08-0x0B)
        self._write_pointer(self.REG_ALERT_CONFIG)
        configs = self._read_bytes(4)
        # read Limits (Reg 0x10-0x17, 2 bytes each)
        self._write_pointer(self.REG_ALERT_LIMIT)
        limits_data = self._read_bytes(8)
        limits = []
        for i in range(0, 8, 2):
            val = (limits_data[i] << 8) | limits_data[i+1]
            if val & 0x8000: val -= 65536
            limits.append(val * 0.0625)
        # read Hysteresis (Reg 0x0C-0x0F)
        self._write_pointer(self.REG_ALERT_HYSTERESIS)
        hyst = self._read_bytes(4)
        return {
            'configs': configs,
            'limits': limits,
            'hysteresis': hyst
        }

    
    def set_alert(self,
                  alert_num,
                  enable=True,
                  limit=150.0,
                  hysteresis=10,
                  monitor='TH',
                  rising=True,
                  active_low=False,
                  mode='comparator',
                  clear_interrupt=False):
        
        """Fully configure an alert (1-4)."""
        assert 1 <= alert_num <= 4
        # calculate limit value (p.37)
        limit_val = int(abs(limit) / 0.0625)
        if limit < 0: limit_val |= 0x8000  # Sign bit
        # write Limit (2 bytes)
        self.i2c.writeto(self.address, bytes([
            self.REG_ALERT_LIMIT + (alert_num - 1),
            (limit_val >> 8) & 0xFF,
            limit_val & 0xFF
        ]))
        # write Hysteresis (1 byte)
        self.i2c.writeto(self.address, bytes([
            self.REG_ALERT_HYSTERESIS + (alert_num - 1),
            min(hysteresis, 255)
        ]))
        # write Config (p.40, Reg 5-11)
        config = 0
        if enable:              config |= 0b00000001
        if mode == 'interrupt': config |= 0b00000010
        if not active_low:      config |= 0b00000100
        if not rising:          config |= 0b00001000
        if monitor == 'TC':     config |= 0b00010000
        if clear_interrupt:     config |= 0b10000000
        
        self.i2c.writeto(self.address, bytes([
            self.REG_ALERT_CONFIG + (alert_num - 1),
            config
        ]))

    
    def get_status(self):
        """
        Read STATUS register (p.33-34, Reg 5-6).
        TC in short-circuit is handled differently by MCP9600 ad MCP9601.
        input_range_error has different meaning, check datasheet.
        """
        self._write_pointer(self.REG_STATUS)
        status = self._read_bytes(1)[0]
        sc = False if self.dev_id == 0x40 else bool(status & (1 << 5))
        return {
        'burst_complete':    bool(status & (1 << 7)),
        'temp_updated':      bool(status & (1 << 6)),
        'short_circuit':     sc,
        'input_range_error': bool(status & (1 << 4)),
        'alerts': [bool(status & (1 << i)) for i in range(4)]
        }
    
    
    def get_alerts(self, alerts=None):
        """
        Read ALERT status register (p.33-34, Reg 5-6).
        
        Args:
            alerts: Can be one of:
                - None (returns all 4 alerts)
                - int (single alert number 1-4)
                - list of ints (specific alert numbers 1-4)
                - range object (e.g., range(1,3) for alerts 1-2)
        
        Returns:
            dict: {alert_number: status} for requested alerts
        """
        # read status register once
        self._write_pointer(self.REG_STATUS)
        status = self._read_bytes(1)[0]
        
        # handle different input types
        if alerts is None:
            alerts = range(1, 5)  # all alerts
        elif isinstance(alerts, int):
            alerts = (alerts)
            print(alerts)
        
        # validate and process alerts
        result = {}
        for alert_num in alerts:
            if not 1 <= alert_num <= 4:
                raise ValueError(f"Alert number must be 1-4, got {alert_num}")
            result[str(alert_num)] = bool(status & (1 << (alert_num - 1)))
        
        return result
