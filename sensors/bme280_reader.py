import time
import board
import busio
from adafruit_bme280 import basic as adafruit_bme280

i2c = busio.I2C(board.SCL, board.SDA)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
bme280.sea_level_pressure = 1013.25

def get_humidity():
    return round(bme280.relative_humidity, 2)

def get_temperature():
    return round(bme280.temperature, 2)

def get_pressure():
    return round(bme280.pressure, 2)