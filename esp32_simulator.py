import json
import time
import paho.mqtt.client as mqtt

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

COMMAND_TOPIC = (
    "airswitch_es_demo_2026_v2/command"
)

STATUS_TOPIC = (
    "airswitch_es_demo_2026_v2/status/local"
)

state = {

    "light": {
        "on": False,
        "brightness": 50
    },

    "fan": {
        "on": False,
        "speed": 50
    },

    "last_gesture": "NONE",

    "device": "Python ESP32 Simulator"
}


def clamp(
    value,
    low=0,
    high=100
):

    return max(
        low,
        min(high, value)
    )


def apply_gesture(gesture):

    # LIGHT ON
    if gesture == "OPEN_PALM":

        state["light"]["on"] = True


    # LIGHT OFF
    elif gesture == "FIST":

        state["light"]["on"] = False


    # LIGHT BRIGHTNESS UP
    elif gesture == "THUMBS_UP":

        state["light"]["on"] = True

        state["light"]["brightness"] = clamp(
            state["light"]["brightness"]
            + 25
        )


    # LIGHT BRIGHTNESS DOWN
    elif gesture == "THUMBS_DOWN":

        state["light"]["on"] = True

        state["light"]["brightness"] = clamp(
            state["light"]["brightness"]
            - 25
        )


    # FAN ON
    elif gesture == "SWIPE_RIGHT":

        state["fan"]["on"] = True


    # FAN OFF
    elif gesture == "SWIPE_LEFT":

        state["fan"]["on"] = False


    # FAN SPEED UP
    elif gesture == "TWO_FINGERS":

        state["fan"]["on"] = True

        state["fan"]["speed"] = clamp(
            state["fan"]["speed"]
            + 25
        )


    # FAN SPEED DOWN
    elif gesture == "THREE_FINGERS":

        state["fan"]["on"] = True

        state["fan"]["speed"] = clamp(
            state["fan"]["speed"]
            - 25
        )


def publish_status(client):

    client.publish(
        STATUS_TOPIC,
        json.dumps(state),
        qos=0,
        retain=True
    )


def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties
):

    print(
        f"MQTT connected: {reason_code}"
    )

    client.subscribe(
        COMMAND_TOPIC
    )

    publish_status(client)


def on_message(
    client,
    userdata,
    msg
):

    try:

        payload = json.loads(
            msg.payload.decode("utf-8")
        )

        gesture = payload.get(
            "gesture",
            "UNKNOWN"
        )

    except Exception:

        print(
            "Invalid MQTT payload"
        )

        return

    print(
        f"Received: {gesture}"
    )

    apply_gesture(
        gesture
    )

    state["last_gesture"] = gesture

    publish_status(
        client
    )

    print(
        f"Light: "
        f"{'ON' if state['light']['on'] else 'OFF'} "
        f"({state['light']['brightness']}%) | "
        f"Fan: "
        f"{'ON' if state['fan']['on'] else 'OFF'} "
        f"({state['fan']['speed']}%)"
    )


def main():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=(
            f"airswitch-python-esp32-"
            f"{int(time.time())}"
        )
    )

    client.on_connect = on_connect
    client.on_message = on_message

    print(
        f"Connecting to "
        f"{MQTT_BROKER}:{MQTT_PORT}..."
    )

    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60
    )

    print(
        "Python ESP32 simulator running."
    )

    print(
        "Waiting for gesture commands..."
    )

    client.loop_forever()


if __name__ == "__main__":
    main()