from machine import Pin, Timer, I2C
import dht
import time
import uasyncio
import gc
from aswitch import Switch, Pushbutton

led2 = Pin(19, Pin.OUT) #green
led4 = Pin(33, Pin.OUT) #red
led = Pin(2, Pin.OUT)

sw = Pin(18, Pin.IN, Pin.PULL_UP)

switch = Pushbutton(sw, suppress = True)


async def blink2(led):
    try:
      while True:
        led.on()
        await uasyncio.sleep_ms(100)
        led.off()
        await uasyncio.sleep_ms(100)

    except uasyncio.CancelledError:
      print('Trapped cancelled error.')
      raise  # Enable check in outer scope
    finally:
      print('Cancelled - finally')



async def blink3(led):
  try:
    while True:
      led.on()
      await uasyncio.sleep_ms(200)
      led.off()
      await uasyncio.sleep_ms(200)
  except uasyncio.CancelledError:
    print('Trapped cancelled error.')
    raise  # Enable check in outer scope
  finally:
    print('Cancelled - finally')


async def nothing():
  await uasyncio.sleep_ms(2)


async def blink(led): # this function blinks the on-board led
    while True:
        led.on()
        await uasyncio.sleep(1)
        led.off()
        await uasyncio.sleep(1)

toggle = False
blink2_task = False
blink3_task = False

def foo():
    global toggle
    global blink2_task
    global blink3_task

    if toggle:
       blink2_task.cancel()
       blink3_task = uasyncio.create_task(blink3(led4))


       print('Toggle')
    else:
        blink2_task = uasyncio.create_task(blink2(led2))
        try: # this is necessary b/c otherwise it throws an attribution error b/c blink3_task is a boolean before assignment
          blink3_task.cancel()
        except:
          pass
        print('Else')
    toggle = not toggle




async def cancel():
    await uasyncio.sleep(120)

def set_global_exception():
    def handle_exception(loop, context):
        import sys
        sys.print_exception(context["exception"])
        sys.exit()
    loop = uasyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)

async def main():
    set_global_exception()  # Debug aid
    switch.release_func(foo, ())
    uasyncio.create_task(blink(led))
    await cancel() # Non-terminating method

try:
    uasyncio.run(main())
finally:
    uasyncio.new_event_loop()  # Clear retained state

gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())
