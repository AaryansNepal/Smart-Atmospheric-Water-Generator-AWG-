from gpiozero import LED, Buzzer

LED_BLUE = 17       # System not running
LED_GREEN = 27      # System running
LED_YELLOW = 22     # No internet
BUZZER = 26         # Tank full

blue_led = LED(LED_BLUE)
green_led = LED(LED_GREEN)
yellow_led = LED(LED_YELLOW)
buzzer = Buzzer(BUZZER)

def indicate_low_humidity():
    blue_led.on()
    green_led.off()

def indicate_good_humidity():
    green_led.on()
    blue_led.off()

# No internet indicator
def indicate_no_internet():
    yellow_led.on()

def stop_no_internet():
    yellow_led.off()

def clear_leds():
    blue_led.off()
    green_led.off()
    yellow_led.off()

def sound_alarm():
    buzzer.on()

def stop_alarm():
    buzzer.off()