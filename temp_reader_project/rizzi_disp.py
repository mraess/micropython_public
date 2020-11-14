
# Rizzimatic
import time
from time import sleep, sleep_ms


def custom_chr_maker(lcd):
  index = 0
  arrow_up = bytearray([0x00,0x04,0x0E,0x1F,0x04,0x04,0x04,0x04])
  arrow_down = bytearray([0x04,0x04,0x04,0x04,0x1F,0x0E,0x04,0x00])
  skull = bytearray([0x00, 0x0E, 0x15, 0x1B, 0x0E, 0x0E, 0x00, 0x00])
  heart = bytearray([0x00,0x0a,0x1f,0x1f,0x0e,0x04,0x00,0x00])
  note = bytearray([0x02,0x03,0x02,0x0e,0x1e,0x0c,0x00,0x00])
  grin = bytearray([0x00,0x00,0x0A,0x00,0x1F,0x11,0x0E,0x00])
  meh = bytearray([0x00,0x0A,0x00,0x04,0x00,0x1F,0x00,0x00])
  happy = bytearray([0x00,0x0A,0x00,0x04,0x00,0x11,0x0E,0x00])
  custom = [arrow_up, arrow_down, skull, heart, note, grin, meh, happy]

  for i in custom:
    lcd.custom_char(index, i)
    index += 1


def rizzimatic(lcd):
    from time import sleep, sleep_ms
    rizzi = ['R', 'i', 'z', 'z', 'i', 'M', chr(2), 't', 'i', 'c']
    thermo = ['T', 'h', 'e', 'r','m','o','C',':','V','1','.','0']
    lcd.move_to(0,0)
    for i in rizzi:
      lcd.putchar(i)
      sleep_ms(110)
    lcd.move_to(3, 1)
    for i in thermo:
      lcd.putchar(i)
      sleep_ms(110)

def rizzi_over(lcd):
      overwrite = [chr(2), chr(0), chr(3), chr(4), chr(2), chr(7), chr(4), chr(2), chr(1), chr(6)]
      lcd.move_to(0,0)
      for i in overwrite:
        lcd.putchar(i)
        sleep_ms(100)


def rizzimatic_clear(lcd):
     lcd.move_to(0,0)
     for i in range(11):
        lcd.putstr(' ')
        sleep_ms(100)
     lcd.move_to(3,1)
     for i in range(12):
         lcd.putstr(' ')
         sleep_ms(100)


def rizzi_run(lcd):
  from time import sleep, sleep_ms
  rizzimatic(lcd)
  sleep_ms(300)
  rizzi_over(lcd)
  sleep_ms(200)
  rizzimatic_clear(lcd)
