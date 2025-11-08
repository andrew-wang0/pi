from gpiozero import MotionSensor, RGBLED, LED, Device
from gpiozero.pins.lgpio import LGPIOFactory
from RPLCD.i2c import CharLCD
from signal import pause
from datetime import date
import threading, os, time, colorsys

Device.pin_factory = LGPIOFactory()

# --- paths & pins ---
messages_dir = "messages"

PIR_PIN = 14

# RGB LED pins (R, G, B) = (16, 20, 21)
RGB_R_PIN = 16
RGB_G_PIN = 20
RGB_B_PIN = 21
COMMON_ANODE = False 

MOTION_LED_PIN = 17

# LCD
I2C_ADDR = 0x27
LCD_COLS, LCD_ROWS = 16, 2

# --- devices ---
pir = MotionSensor(PIR_PIN)
rgb = RGBLED(RGB_R_PIN, RGB_G_PIN, RGB_B_PIN, pwm=True, active_high=not COMMON_ANODE)
motion_led = LED(MOTION_LED_PIN)

lcd = CharLCD('PCF8574', address=I2C_ADDR, port=1,
              cols=LCD_COLS, rows=LCD_ROWS,
              backlight_enabled=False)

# --- rainbow control ---
_rainbow_on = False
_rainbow_lock = threading.Lock()

def _rainbow_loop():
    h = 0.0
    while True:
        with _rainbow_lock:
            if not _rainbow_on:
                break
        r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
        rgb.color = (r, g, b)
        time.sleep(0.015)
        h = (h + 0.004) % 1.0

def _start_rainbow():
    global _rainbow_on
    with _rainbow_lock:
        if _rainbow_on:
            return
        _rainbow_on = True
    threading.Thread(target=_rainbow_loop, daemon=True).start()

def _stop_rainbow():
    global _rainbow_on
    with _rainbow_lock:
        _rainbow_on = False

def _set_idle_color():
    rgb.color = (0.05, 0.03, 0.0)

# Initial LED/LCD state
_set_idle_color()
lcd.clear()
lcd.backlight_enabled = False
motion_led.off()

# --- timing (shared by LCD + rainbow) ---
CLEAR_SECONDS = 10.0
_clear_timer = None
_timer_lock = threading.Lock()

def _schedule_clear():
    global _clear_timer
    with _timer_lock:
        if _clear_timer and _clear_timer.is_alive():
            _clear_timer.cancel()
        _clear_timer = threading.Timer(CLEAR_SECONDS, _timeout_clear)
        _clear_timer.daemon = True
        _clear_timer.start()

def _timeout_clear():
    lcd.clear()
    lcd.backlight_enabled = False
    _stop_rainbow()
    _set_idle_color()
    # motion_led stays off unless a new motion event arrives

# --- message helpers ---
def _load_message_for_today():
    today_fname = os.path.join(messages_dir, date.today().strftime("%Y-%m-%d"))
    default_fname = os.path.join(messages_dir, "default")

    if os.path.exists(today_fname):
        with open(today_fname, "r", encoding="utf-8") as f:
            return f.read().strip() or "Welcome!"
    if os.path.exists(default_fname):
        with open(default_fname, "r", encoding="utf-8") as f:
            return f.read().strip() or "Welcome!"
    return "Welcome!"

def _write_message_to_lcd(text):
    """Write safely to 16x2 (clip to width, 2 lines)."""
    lcd.clear()
    lcd.backlight_enabled = True
    lines = text.splitlines()
    line1 = (lines[0] if len(lines) > 0 else "")[:LCD_COLS]
    line2 = (lines[1] if len(lines) > 1 else "")[:LCD_COLS]
    lcd.write_string(line1)
    lcd.crlf()
    lcd.write_string(line2)

# --- PIR handlers ---
def on_motion():
    # Motion indicator LED ON only while actively detecting
    motion_led.on()

    # Start/continue rainbow for the full hold duration
    _start_rainbow()

    # Update the display
    msg = _load_message_for_today()
    _write_message_to_lcd(msg)

    # Reset the hold timer (affects both screen and rainbow)
    _schedule_clear()

def on_no_motion():
    # Turn OFF the motion indicator LED immediately
    motion_led.off()

    # Keep rainbow + LCD until timeout expires
    _schedule_clear()

pir.when_motion = on_motion
pir.when_no_motion = on_no_motion

pause()
