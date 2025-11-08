from time import sleep
from RPLCD.i2c import CharLCD

lcd = CharLCD('PCF8574', address=0x27, port=1, cols=16, rows=2,
              backlight_enabled=False)   # start OFF

sleep(1)
lcd.backlight_enabled = True   # ON
sleep(1)
lcd.backlight_enabled = False  # OFF
sleep(1)
lcd.close(clear=False)
