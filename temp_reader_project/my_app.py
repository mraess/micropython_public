
from machine import Pin, Timer, I2C, SPI
import time
import uasyncio
import gc
from aswitch import Switch, Pushbutton
from encoder import Encoder
from esp8266_i2c_lcd import I2cLcd

i2c = I2C(-1, scl=Pin(22), sda=Pin(21))
cs = Pin(5, Pin.OUT)
spi = SPI(-1, baudrate=5000000, polarity=0, phase=0, sck=Pin(33), mosi = Pin(10), miso=Pin(19))

class tempReader():

  sleep = 1 #static instance variable for testing
  temp_l = []
  temp_t = []
  saved_rot = [0]
  diff = []
  alert_res = []


  def __init__(self, led, sensor, cs, spi, enc, lcd, np):
    self.led = led
    self.sensor = sensor
    self.cs = cs
    self.spi = spi
    self.lcd = lcd
    self.enc = enc
    self.np = np
    #self.enc_cur_val = 511
    self.fader_target_val = 0
    #self.pressed = False # Has the button been pressed?
    #self.on = False # State of the LED strip

  # clear lcd
  def lcd_clear(self):
    self.lcd.move_to(0, 0)
    self.lcd.putstr(" " * 80)

  # show text on lcd
  def lcd_show(self, text, line):
    self.lcd.move_to(0, line)
    self.lcd.putstr(text)

  def clear_cell(self,x,y): #16 is a blank character in the Japanese charater set
    self.lcd.move_to(x,y)
    self.lcd.putchar(chr(16))

  def place_chr_at_position(self,x,y): #degree symbol
    self.lcd.move_to(x,y)
    self.lcd.putchar(chr(223))

  def clear_np(self,n):
    for i in range(n):
        self.np[i] = (0,0,0)
    self.np.write()

  def set_np_col(self,c,n):
    if c == 1:
        self.np[n] = (0,255,0)
    if c == 2:
        self.np[n] = (255,100,0)
    if c == 3:
        self.np[n] = (0,0,255)
    self.np.write()

  async def blink(self): # this function blinks the on-board led
    while True:
        self.led.on()
        await uasyncio.sleep(tempReader.sleep)
        self.led.off()
        await uasyncio.sleep(tempReader.sleep)

  async def temp(self): #this function reads the temperature from the sensor every 2 seconds and appeds reading to list
    while True:
      #self.sensor.measure()
      temp = self.sensor.read_compensated_data()
      tempReader.temp_l.clear()
      tempReader.temp_l.append(self.sensor.read_compensated_data())
      #print('Temperature: {} C'.format(temp[0]))
      #print('Humidity: {}%'.format(temp[2]))
      #print('Pressure: {} hPa'.format(temp[1]/100))
      #print(tempReader.temp_l[0])
      await uasyncio.sleep(2)

  async def temp_thermo(self):
    while True:
        try:
            data = bytearray(4)
            self.cs.value(0)
            self.spi.readinto(data)
            self.cs.value(1)
            #print(data)
            temp = data[0] << 8 | data[1]
            if temp & 0x0001:
                return float('NaN')
            temp >>= 2
            if temp & 0x2000:
               temp -= 16384
            #print((temp * 0.25) - 5)
            tempReader.temp_t.clear()
            tempReader.temp_t.append((temp*0.25)- 3) #adjust for temperature diff
            print(tempReader.temp_t[0])
        except:
            pass
        await uasyncio.sleep_ms(500)


  async def encoder_loop(self, enc):

        oldval = 30

        while True:
                self.enc_cur_val = enc.value/2
                enc.cur_accel = max(0, enc.cur_accel - enc.accel)
                if oldval != self.enc_cur_val:
                    #print('Old enc. val: %i, new enc. val: %i' % (oldval, self.enc_cur_val))
                    self.fader_target_val = oldval = self.enc_cur_val
                    if len(tempReader.saved_rot) != 0:
                      tempReader.saved_rot.clear()
                      tempReader.saved_rot.append(self.fader_target_val)
                    else:
                      tempReader.saved_rot.append(self.fader_target_val)
                await uasyncio.sleep_ms(50)

  async def calc_diff(self):
      while True:
          if tempReader.saved_rot[0] != 0:
              tempReader.diff.clear()
              tempReader.diff.append(tempReader.saved_rot[0] - tempReader.temp_t[0])
          else:
              print('bs')
          await uasyncio.sleep_ms(1000)

  async def alert_check(self):
      while True:
          if tempReader.saved_rot[0] != 0:
               if abs(round(tempReader.temp_t[0]/tempReader.saved_rot[0],2)) >= 1.2:
                    print('20%')
                    tempReader.alert_res.clear()
                    tempReader.alert_res.append('20%')
               elif abs(round(tempReader.temp_t[0]/tempReader.saved_rot[0],2)) >= 1:
                    print('over_100')
                    tempReader.alert_res.clear()
                    tempReader.alert_res.append('over_100')
               elif abs(round(tempReader.temp_t[0]/tempReader.saved_rot[0],2)) >= .8:
                    print('80%')
                    tempReader.alert_res.clear()
                    tempReader.alert_res.append('80%')
               elif abs(round(tempReader.temp_t[0]/tempReader.saved_rot[0],2)) >= .5:
                    print('50%')
                    tempReader.alert_res.clear()
                    tempReader.alert_res.append('50%')
               elif abs(round(tempReader.temp_t[0]/tempReader.saved_rot[0],2)) >= 1.2:
                    print('20%')
                    tempReader.alert_res.clear()
                    tempReader.alert_res.append('20%')

               else:
                print('ok')
                tempReader.alert_res.clear()
                tempReader.alert_res.append('ok')

          elif tempReader.saved_rot[0] == 0:
               if round((0/tempReader.temp_t[0]),2) in (p/100 for p in range(60,120)):
                print('yes')
               else:
                print('no')

          await uasyncio.sleep_ms(500)

  async def show_lcd(self):

    arrow_up = bytearray([0x00,0x04,0x0E,0x1F,0x04,0x04,0x04,0x04])
    arrow_down = bytearray([0x04,0x04,0x04,0x04,0x1F,0x0E,0x04,0x00])
    self.lcd.custom_char(0, arrow_up)
    self.lcd.custom_char(1, arrow_down)

    try:
        while True:
          self.lcd_show('Temp: %3.1f' %tempReader.temp_t[0], 0)
          self.place_chr_at_position(10,0)
          if len(tempReader.diff) != 0:
              self.lcd_show('Set: {tem}  {tem2:1.1f}'.format(tem2 = tempReader.diff[0], tem = tempReader.saved_rot[0]),1)
              if tempReader.diff[0] > 0:
                  self.lcd.move_to(10,1)
                  self.lcd.putchar(chr(1))
              elif tempReader.diff[0] < 0:
                  self.lcd.move_to(10,1)
                  self.lcd.putchar(chr(0))
          else:
              self.lcd_show('Set: {tem} D: NA'.format(tem = tempReader.saved_rot[0]) ,1)

          if tempReader.alert_res[0] == 'over_100':
              self.lcd.move_to(11,0)
              self.lcd.putstr('above')
          elif tempReader.alert_res[0] == '80%':
              self.lcd.move_to(11,0)
              self.lcd.putstr('80%  ')
          elif tempReader.alert_res[0] == '50%':
              self.lcd.move_to(11,0)
              self.lcd.putstr('50%  ')
          elif tempReader.alert_res[0] == '20%':
              self.lcd.move_to(11,0)
              self.lcd.putstr('below')
          else:
              for i in range(11,16):
                  self.lcd.move_to(i,0)
                  self.lcd.putstr(' ')

          await uasyncio.sleep_ms(200)

    except uasyncio.CancelledError:
        print('Trapped cancelled error.')
        raise  # Enable check in outer scope
    finally:
        print('Cancelled - finally')

  async def alert_light(self):
      while True:
          if tempReader.alert_res[0] == 'over_100':
            self.set_np_col(1,0)
          elif tempReader.alert_res[0] == '80%':
            self.set_np_col(2,0)
          elif tempReader.alert_res[0] == '50%':
            self.set_np_col(3,0)
          else:
             self.clear_np(1)
          await uasyncio.sleep_ms(100)

  async def show_lcd_2(self):
    try:
        if len(tempReader.temp_l) != 0:
            while True:

              self.lcd_show('{temp:.2f} C {hum:.2f}%rh'.format(temp = tempReader.temp_l[0][0], hum = tempReader.temp_l[0][2]), 0)
              self.place_chr_at_position(5,0)
              self.lcd_show('{hPa:.2f} hPa'.format(hPa = (tempReader.temp_l[0][1]/100)),1)
              await uasyncio.sleep_ms(500)
        else:
              pass
    except uasyncio.CancelledError:
        print('Trapped cancelled error.')
        raise  # Enable check in outer scope
    finally:
        print('Cancelled - finally')

  async def show_lcd_initial(self):
    try:
        if len(tempReader.temp_l) != 0:

              self.lcd_show('{temp:.2f} C {hum:.2f}%rh'.format(temp = tempReader.temp_l[0][0], hum = tempReader.temp_l[0][2]), 0)
              self.place_chr_at_position(5,0)
              self.lcd_show('{hPa:.2f} hPa'.format(hPa = (tempReader.temp_l[0][1]/100)),1)
              await uasyncio.sleep_ms(500)
        else:
              pass
    except uasyncio.CancelledError:
        print('Trapped cancelled error.')
        raise  # Enable check in outer scope
    finally:
        print('Cancelled - finally')


  async def cancel(self):
    await uasyncio.sleep(20) #stops the loop after 10 seconds
