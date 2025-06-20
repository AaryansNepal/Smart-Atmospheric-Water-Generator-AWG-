import time
import RPi.GPIO as GPIO
from AWG.sensors.bme280_reader import get_humidity
from AWG.sensors.distance_sensor import get_water_distance, is_tank_full, calibrate_tank_height
from AWG.actuators.relay_control import turn_on_awg, turn_off_awg
from AWG.actuators.leds import indicate_low_humidity, indicate_good_humidity, sound_alarm, stop_alarm, indicate_no_internet, stop_no_internet
from AWG.actuators.lcd_display import display_status
from AWG.utils.constants import HUMIDITY_THRESHOLD, DEFAULT_TANK_HEIGHT, DEFAULT_FULL_TRIGGER_DISTANCE
from AWG.utils.tank_config import load_tank_height, save_tank_height
from AWG.network.mqtt_handler import publish_sensor_data
from AWG.network.connectivity import is_connected
from AWG.utils.logger import save_locally

SYNC_BUTTON_PIN = 16
GPIO.setup(SYNC_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# GPIO for calibration button
CALIBRATION_BUTTON_PIN = 5
GPIO.setmode(GPIO.BCM)
GPIO.setup(CALIBRATION_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initial variables
FULL_TRIGGER_DISTANCE = None
AWG_RUNNING = False
humidity = None
bme_ok = False
session_id = 1
reading_counter = 0

# Timers
BME_CHECK_INTERVAL = 7200  # every 2 hours
DIST_CHECK_INTERVAL = 10   # every 10 seconds
last_bme_check = 0

# Load saved tank height or fallback
height = load_tank_height()
if height:
    FULL_TRIGGER_DISTANCE = round(height * 0.15, 3)
    print(f"[LOAD] Using saved tank height: {height:.3f} m → Trigger at {FULL_TRIGGER_DISTANCE:.3f} m")
else:
    FULL_TRIGGER_DISTANCE = DEFAULT_FULL_TRIGGER_DISTANCE
    print("[FALLBACK] No saved height. Using default tank height.")


# --- Main loop ---
while True:
    current_time = time.time()
    distance = None
    distance_ok = True

    # --- 1. Check BME280 every 2 hrs ---
    if current_time - last_bme_check >= BME_CHECK_INTERVAL or humidity is None:
        try:
            humidity = get_humidity()
            bme_ok = True
            last_bme_check = current_time
            reading_counter += 1
            print(f"Humidity: {humidity:.1f}%")

            # --- 2. Record this reading (MQTT or local) ---
            distance_for_log = get_water_distance()
            if is_connected():
                success = publish_sensor_data(session_id, reading_counter, humidity, distance_for_log)
                if not success:
                    save_locally(session_id, reading_counter, humidity, distance_for_log)
                stop_no_internet()
            else:
                save_locally(session_id, reading_counter, humidity, distance_for_log)
                indicate_no_internet()


        except Exception as e:
            print(f"[BME280 ERROR] {e}")
            bme_ok = False
            humidity = None

    # --- 3. Check distance every 10 seconds ---
    try:
        distance = get_water_distance()
        if distance is not None:
            print(f"Water Level: {distance:.2f} m")
            distance_ok = True
        else:
            print("[Distance] No reading")
            distance_ok = False
    except Exception as e:
        print(f"[Distance ERROR] {e}")
        distance = None
        distance_ok = False

    # --- 4. Safety check: hard stop if distance too low ---
    SAFETY_MIN_DISTANCE = 0.05  # 5 cm

    if distance is not None and distance < SAFETY_MIN_DISTANCE:
        print(f"[SAFETY] Distance {distance:.2f} m is below {SAFETY_MIN_DISTANCE:.2f} m → Stopping AWG immediately.")
        indicate_low_humidity()
        stop_alarm()
        turn_off_awg()
        AWG_RUNNING = False
        display_status(humidity, distance, bme_ok, distance_ok)
        time.sleep(DIST_CHECK_INTERVAL)
        continue  # skip rest of the loop

    # --- 5. Determine system status ---
    humidity_ok = bme_ok and humidity is not None and humidity >= HUMIDITY_THRESHOLD
    tank_full = is_tank_full(distance, FULL_TRIGGER_DISTANCE)

    # --- 6. AWG logic ---
    if humidity_ok and not tank_full:
        if not AWG_RUNNING:
            session_id += 1  # New session when AWG starts
        indicate_good_humidity()
        stop_alarm()
        turn_on_awg()
        AWG_RUNNING = True
    elif tank_full:
        print("Stopping: Tank full.")
        indicate_low_humidity()
        sound_alarm()
        turn_off_awg()
        AWG_RUNNING = False
    else:
        print("Stopping: Humidity low or sensor error.")
        indicate_low_humidity()
        stop_alarm()
        turn_off_awg()
        AWG_RUNNING = False

    # --- 7. LCD display ---
    display_status(humidity, distance, bme_ok, distance_ok)

    # --- 8. Wait + check for sync button every 0.1s during distance delay ---
    WAIT_TIME = DIST_CHECK_INTERVAL  # 10 seconds
    TICK = 0.1  # check every 0.1s
    elapsed = 0

    from AWG.utils.logger import LOG_PATH
    import json

    while elapsed < WAIT_TIME:
        if GPIO.input(SYNC_BUTTON_PIN) == GPIO.LOW:
            print("[SYNC] Sync button pressed!")
            time.sleep(0.5)  # debounce

            if is_connected():
                stop_no_internet()
                try:
                    if LOG_PATH.exists():
                        with open(LOG_PATH, "r") as f:
                            data = json.load(f)

                        if not data:
                            print("[SYNC] No offline data found.")
                        else:
                            for entry in data:
                                success = publish_sensor_data(
                                    entry["session"],
                                    entry["reading"],
                                    entry["humidity"],
                                    entry["water_level"]
                                )
                                if not success:
                                    print("[SYNC] Failed to send one entry. Stopping sync.")
                                    break
                            else:
                                with open(LOG_PATH, "w") as f:
                                    json.dump([], f)
                                print("[SYNC] All offline data pushed and cleared.")
                    else:
                        print("[SYNC] data_log.json not found.")
                except Exception as e:
                    print(f"[SYNC ERROR] {e}")
            else:
                indicate_no_internet()
                print("[SYNC] No internet. Cannot sync now.")

        # --- Check for calibration button press ---
        if GPIO.input(CALIBRATION_BUTTON_PIN) == GPIO.LOW:
            print("[CALIBRATION] Button pressed. Recalibrating tank height...")
            new_height = calibrate_tank_height()
            if new_height:
                save_tank_height(new_height)
                FULL_TRIGGER_DISTANCE = round(new_height * 0.15, 3)
                print(f"[CALIBRATION] New height: {new_height:.3f} m → Trigger at {FULL_TRIGGER_DISTANCE:.3f} m")
            else:
                print("[CALIBRATION ERROR] Calibration failed. Retaining previous config.")
            time.sleep(0.5)  # Debounce

        time.sleep(TICK)
        elapsed += TICK

    # --- 9. Wait for distance check ---
    time.sleep(DIST_CHECK_INTERVAL)
