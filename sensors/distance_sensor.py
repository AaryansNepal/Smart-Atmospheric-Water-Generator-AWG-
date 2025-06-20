import time
import RPi.GPIO as GPIO
from AWG.utils.constants import TRIG_PIN, ECHO_PIN

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

def get_water_distance():
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.05)

    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    timeout = time.time() + 0.04
    while GPIO.input(ECHO_PIN) == 0:
        if time.time() > timeout:
            print("[HC-SR04] Echo not received (start)")
            return None
    start = time.time()

    timeout = time.time() + 0.04
    while GPIO.input(ECHO_PIN) == 1:
        if time.time() > timeout:
            print("[HC-SR04] Echo stuck high (end)")
            return None
    end = time.time()

    elapsed = end - start
    distance = (elapsed * 34300) / 2 / 100  # convert to meters

    if distance > 1.0 or distance < 0.005:
        print(f"[HC-SR04] Invalid reading: {distance:.2f} m")
        return None

    return round(distance, 3)

def is_tank_full(distance, full_threshold):
    return distance is not None and distance <= full_threshold

def calibrate_tank_height():
    print("[CALIBRATION] Measuring empty tank height...")
    reading = get_water_distance()

    if reading is None or reading < 0.05:
        print("[ERROR] Invalid calibration distance")
        return None

    print(f"[CALIBRATION] Tank height = {reading:.2f} m")
    return reading
