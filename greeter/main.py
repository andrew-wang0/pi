from gpiozero import MotionSensor, LED
from signal import pause

# BCM pin numbers
PIR_PIN = 4
MOTION_LED_PIN = 17
IDLE_LED_PIN = 26

pir = MotionSensor(PIR_PIN)          # expects HIGH on motion, LOW otherwise
motion_led = LED(MOTION_LED_PIN)
idle_led = LED(IDLE_LED_PIN)

# Start with idle LED on (no motion yet)
idle_led.on()
motion_led.off()

def on_motion():
    motion_led.on()
    idle_led.off()
    print("Motion detected")

def on_no_motion():
    motion_led.off()
    idle_led.on()
    print("No motion")

pir.when_motion = on_motion
pir.when_no_motion = on_no_motion

print("PIR ready. Waiting for motion...")
pause()
