import json
import time

import paho.mqtt.client as mqtt


BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC = (
    "airswitch_es_demo_2026_v2/command"
)


SEQUENCE = [

    "OPEN_PALM",

    "THUMBS_UP",
    "THUMBS_UP",

    "THUMBS_DOWN",

    "FIST",

    "SWIPE_RIGHT",

    "TWO_FINGERS",
    "TWO_FINGERS",

    "THREE_FINGERS",

    "SWIPE_LEFT"
]


def main():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=(
            f"airswitch-test-"
            f"{int(time.time())}"
        )
    )

    client.connect(
        BROKER,
        PORT,
        60
    )

    client.loop_start()


    for gesture in SEQUENCE:

        payload = {

            "gesture": gesture,

            "source": "test_commands",

            "timestamp": time.time()
        }


        client.publish(
            TOPIC,
            json.dumps(payload)
        )


        print(
            f"Sent: {gesture}"
        )


        time.sleep(1.2)


    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":

    main()