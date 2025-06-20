import time
from AWG.actuators import I2C_LCD_driver

try:
    lcd = I2C_LCD_driver.lcd()
    lcd_ok = True
except Exception as e:
    print(f"[LCD INIT ERROR] {e}")
    lcd_ok = False

def display_status(humidity=None, distance=None, bme_ok=True, distance_ok=True):
    if not lcd_ok:
        print("[LCD] Not available. Skipping update.")
        return

    try:
        lcd.lcd_clear()
        if not bme_ok:
            lcd.lcd_display_string("Humidity: N/A", 1)
            lcd.lcd_display_string("BME280 Failed", 2)
        elif not distance_ok:
            lcd.lcd_display_string(f"Hum: {humidity:.1f}%", 1)
            lcd.lcd_display_string("Dist: N/A", 2)
        else:
            lcd.lcd_display_string(f"Hum: {humidity:.1f}%", 1)
            lcd.lcd_display_string(f"Lvl: {distance:.2f}m", 2)

    except Exception as e:
        print(f"[LCD UPDATE ERROR] {e}")
