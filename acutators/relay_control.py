from gpiozero import LED

RELAY_GPIO = 19
relay = LED(RELAY_GPIO)

def turn_on_awg():
    relay.on()

def turn_off_awg():
    relay.off()