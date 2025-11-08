from gpiozero import MotionSensor, LED, Device
from gpiozero.pins.lgpio import LGPIOFactory
from RPLCD.i2c import CharLCD
from signal import pause
import datetime, threading
from datetime import date
import os

messages_dir = "messages"

PIR_PIN = 14
MOTION_LED_PIN = 17
IDLE_LED_PIN = 26

pir = MotionSensor(PIR_PIN)
motion_led = LED(MOTION_LED_PIN)
idle_led = LED(IDLE_LED_PIN)

lcd = CharLCD('PCF8574', address=0x27, port=1, cols=16, rows=2,
              backlight_enabled=False)  # start dark

idle_led.on()
motion_led.off()
lcd.clear()

CLEAR_SECONDS = 15.0
_clear_timer = None
_lock = threading.Lock()

def _schedule_clear():
    global _clear_timer
    with _lock:
        if _clear_timer and _clear_timer.is_alive():
            _clear_timer.cancel()
        _clear_timer = threading.Timer(CLEAR_SECONDS, _clear_lcd)
        _clear_timer.daemon = True
        _clear_timer.start()

def _clear_lcd():
    lcd.clear()
    lcd.backlight_enabled = False

def on_motion():
    motion_led.on()
    idle_led.off()
    lcd.backlight_enabled = True
    lcd.clear()

    fname = os.path.join(messages_dir, date.today().strftime("%Y-%m-%d"))

    if os.path.exists(fname):
        with open(fname) as f:
            message = f.read()
    else:
        with open(os.path.join(messages_dir, "default")) as f:
            meessage = f.read()

    lcd.write_string(message)


    _schedule_clear()

def on_no_motion():
    motion_led.off()
    idle_led.on()
    _schedule_clear()  # keep backlight on until timeout

pir.when_motion = on_motion
pir.when_no_motion = on_no_motion

pause()
