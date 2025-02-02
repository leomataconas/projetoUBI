import RPi.GPIO as GPIO
import time

RELAY_PIN = 17  # GPIO connected to relay IN pin

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

try:
    while True:
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Activate relay (unlock)
        time.sleep(5)                      # Keep unlocked for 5 seconds
        GPIO.output(RELAY_PIN, GPIO.LOW)   # Deactivate relay (lock)
        time.sleep(5)
except KeyboardInterrupt:
    GPIO.cleanup()  # Cleanup GPIO on exit

