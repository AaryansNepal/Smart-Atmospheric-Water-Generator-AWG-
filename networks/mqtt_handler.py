import paho.mqtt.client as mqtt

def publish_sensor_data(session, reading, humidity, water_level):
    client = mqtt.Client()
    try:
        client.connect(BROKER, PORT, 60)
        payload = {
            "session": session,
            "reading": reading,
            "humidity": humidity,
            "water_level": water_level
        }
        client.publish(TOPIC, json.dumps(payload))
        client.disconnect()
        print("[MQTT] Data published.")
        return True
    except Exception as e:
        print(f"[MQTT ERROR] {e}")
        return False  # ← This ensures fallback happens