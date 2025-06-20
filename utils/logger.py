import os
import time

LOG_FILE = "/home/pi/awg_log.txt"


def log_event(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    try:
        with open(LOG_FILE, "a") as log:
            log.write(log_entry)
    except IOError:
        print("[LOGGER] Failed to write to log file.")


def log_sensor_data(humidity, distance, awg_status):
    message = f"Humidity: {humidity}%, Distance: {distance:.2f}m, AWG: {'ON' if awg_status else 'OFF'}"
    log_event(message)