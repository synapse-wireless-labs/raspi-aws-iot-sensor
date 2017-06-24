from __future__ import print_function

#!/usr/bin/env python
#
# Bitbang'd SPI interface with an MCP3008 ADC device
# MCP3008 is 8-channel 10-bit analog to digital converter
#  Connections are:
#     CLK => SCLK
#     DOUT =>  MISO
#     DIN => MOSI
#     CS => CE0

import sys
import spidev


class SpiSensor(object):
    """ A sensor attached to the ADC on the SPI bus
        Params:
        channel - which ADC channel is this sensor attached to
        avg_length - how many samples do you want to average together
        max_value - the max cooked value that the sensor will report
        offset - the number of ADC ticks to offset the reading for calibration
        name - name of sensor
        truncate - truncate the final cooked value to tenths
        verbose - enable print statments
     """

    TICKS_MIN = 818.0
    TICKS_MAX = 4095.0

    def __init__(self, channel, name, type_str, description, avg_length, max_value, offset, truncate=True, verbose=False):
        """Return a sensor object"""
        if channel > 7 or channel < 0:
            return -1

        self.channel = channel
        self.avg_length = avg_length
        self.max_value = max_value
        self.offset = offset
        self.name = name
        self.type = type_str
        self.description = description
        self.truncate = truncate
        self.verbose = verbose
        self.factor = self.max_value/(self.TICKS_MAX - self.TICKS_MIN)
        self.spi = spidev.SpiDev()

    def get_sensor_name(self):
        return self.name

    def get_sensor_type(self):
        return self.type

    def get_sensor_description(self):
        return self.description

    def get_sensor_reading(self):
        """Gets a cooked sensor reading"""
        try:
            self.spi.open(bus=0, device=0)
            val = self.read_adc_avg()
            self.spi.close()
            if self.verbose:
                print("ADC Result: Channel({c}): {v}".format(c=self.channel,v=val))
            val = self.cook_result(val)
            if self.verbose:
                print("Cooked Result: Channel({c}): {v}".format(c=self.channel,v=val))
            return val
        except KeyboardInterrupt:
            self.spi.close()
            sys.exit(0)

    def read_adc_avg(self):
        """Performs an averaged reading for the configured channel"""
        count = self.avg_length
        result = 0
        while count > 0:
            r = self.spi.xfer2(self.__build_read_command(self.channel))
            result += self.__process_adc_value(r)
            count -= 1
        result /= self.avg_length
        return result + self.offset

    def cook_result(self, ticks):
        """Return sensor reading"""
        value = (ticks - self.TICKS_MIN)*self.factor
        if value < 0.000:
            value = 0.000
        if self.truncate:
            value =  self.__truncate(value,1)
        return value

    """ Helper functions """
    @staticmethod
    def __build_read_command(channel):
        start_bit = 0xC0
        return [start_bit |(channel << 3), 0, 0, 0]

    @staticmethod
    def __process_adc_value(result):
        """Take in result as array of three bytes. 
           Return the four lowest bits of the 2nd byte and
           all of the third byte."""
        return (result[0] << 16 | result[1] << 8 | result[2]) >> 5

    @staticmethod
    def __truncate(f, n):
        '''Truncates/pads a float f to n decimal places without rounding'''
        s = '{}'.format(f)
        if 'e' in s or 'E' in s:
            return '{0:.{1}f}'.format(f, n)
        i, p, d = s.partition('.')
        return '.'.join([i, (d+'0'*n)[:n]])
