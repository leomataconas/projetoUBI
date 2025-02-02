import RPi.GPIO as GPIO
import time
from mfrc522 import SimpleMFRC522

# GPIO pin for relay
RELAY_PIN = 18  # GPIO connected to relay IN pin
AUTHORIZED_ID = '162440107148'  # Authorized RFID tag ID

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)  # Initially lock the door

# Initialize RFID reader
reader = SimpleMFRC522()

try:
    while True:
        print("Scan your RFID tag...")
        id, text = reader.read()
        print(f"Card ID: {id}")
        
        if str(id) == AUTHORIZED_ID:
            print("Access Granted: Door is opened!")
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Unlock the door
            time.sleep(5)                     # Keep unlocked for 5 seconds
            GPIO.output(RELAY_PIN, GPIO.HIGH) # Lock the door again
        else:
            print("Access Denied: Door remains locked.")
        time.sleep(1)  # Small delay before next scan

except KeyboardInterrupt:
    GPIO.cleanup()  # Cleanup GPIO on exit
