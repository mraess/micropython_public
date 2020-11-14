

from machine import Pin, Timer, I2C, SPI
import time
import uasyncio
import gc
from aswitch import Switch, Pushbutton
from encoder import Encoder
from my_app import tempReader
from esp8266_i2c_lcd import I2cLcd
from bme280 import BME280
from neopixel import NeoPixel

# Set up peripherals

led = Pin(2, Pin.OUT)

sw = Pin(18, Pin.IN, Pin.PULL_UP)

i2c = I2C(-1, scl=Pin(22), sda=Pin(21)) #i2c setup

sensor = BME280(i2c = i2c, mode = 4) #temp, hum, pressure sensor

lcd = I2cLcd(i2c, 0x27, 4, 20) #lcd display setup

# rotary encoder setup
enc = Encoder(pin_clk= 39, pin_dt = 36, pin_mode=Pin.PULL_UP,
                  min_val=0, max_val=250, clicks=4, init_val=280, reverse = True)
#enc._value = 0

# SPI setup for thermocouple
cs = Pin(5, Pin.OUT) #chip select

spi = SPI(-1, baudrate=5000000, polarity=0, phase=0, sck=Pin(33), mosi = Pin(10), miso=Pin(19))
# MOSI has to be defined BUT is not needed to read data

# neopixel setup

np = NeoPixel(Pin(17), 5)

# Instantiate class

thermo = tempReader(led, sensor, cs, spi, enc, lcd, np)

# Set up display switcher

toggle = False
lcd1_task = False
lcd2_task = False

def switch_display():
    global toggle
    global lcd1_task
    global lcd2_task
    global thermo

    if toggle:
       lcd2_task.cancel() #makes sure only one function output is displayed
       thermo.lcd_clear()
       lcd1_task = uasyncio.create_task(thermo.show_lcd_2())


       print('Toggle')
    else:
        thermo.lcd_clear()
        lcd2_task = uasyncio.create_task(thermo.show_lcd())
        try: # this is necessary b/c otherwise it throws an attribution error b/c lcd2_task is a boolean before assignment
          lcd1_task.cancel()
        except:
          pass
        print('Else')
    toggle = not toggle

async def nothing():
  await uasyncio.sleep_ms(2)


# Setup async app-run

def set_global_exception():
    def handle_exception(loop, context):
        import sys
        sys.print_exception(context["exception"])
        sys.exit()
    loop = uasyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)

async def main():
    global thermo
    set_global_exception()  # Debug aid
    switch = Pushbutton(sw, suppress = True)
    switch.release_func(switch_display, ())

    uasyncio.create_task(thermo.blink()) # Or you might do this
    #uasyncio.create_task(thermo.temp())
    uasyncio.create_task(thermo.temp_thermo())
    uasyncio.create_task(thermo.encoder_loop(enc))

    uasyncio.create_task(thermo.calc_diff())
    uasyncio.create_task(thermo.alert_check())
    uasyncio.create_task(thermo.alert_light())

    uasyncio.create_task(thermo.show_lcd_initial()) #makes sure that something shows up initially

    #await thermo.cancel() # Non-terminating method
    await thermo.temp()
try:
    uasyncio.run(main())
finally:
    uasyncio.new_event_loop()  # Clear retained state


gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
