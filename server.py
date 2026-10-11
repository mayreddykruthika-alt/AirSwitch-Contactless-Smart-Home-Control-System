import json
import time

from flask import (
    Flask,
    jsonify,
    render_template,
    request
)

import paho.mqtt.client as mqtt


MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

COMMAND_TOPIC = (
    "airswitch_es_demo_2026_v2/command"
)

LOCAL_STATUS_TOPIC = (
    "airswitch_es_demo_2026_v2/status/local"
)

WOKWI_STATUS_TOPIC = (
    "airswitch_es_demo_2026_v2/status/wokwi"
)


app = Flask(__name__)


latest = {

    "local": {

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
    },


    "wokwi": {

        "light": {
            "on": False,
            "brightness": 50
        },

        "fan": {
            "on": False,
            "speed": 50
        },

        "last_gesture": "NONE",

        "device": "Wokwi ESP32"
    }
}


def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties
):

    print(
        f"Dashboard MQTT connected: "
        f"{reason_code}"
    )

    client.subscribe(
        LOCAL_STATUS_TOPIC
    )

    client.subscribe(
        WOKWI_STATUS_TOPIC
    )


def on_message(
    client,
    userdata,
    msg
):

    try:

        data = json.loads(
            msg.payload.decode(
                "utf-8"
            )
        )

    except Exception:

        return


    if msg.topic == LOCAL_STATUS_TOPIC:

        latest["local"] = data


    elif msg.topic == WOKWI_STATUS_TOPIC:

        latest["wokwi"] = data


mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=(
        f"airswitch-dashboard-"
        f"{int(time.time())}"
    )
)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)

mqtt_client.loop_start()


@app.route("/")
def index():

    return render_template(
        "index.html"
    )


@app.get("/api/state")
def api_state():

    return jsonify(
        latest
    )


@app.post("/api/command")
def api_command():

    body = (
        request.get_json(
            silent=True
        )
        or {}
    )

    gesture = body.get(
        "gesture"
    )


    allowed = {

        "OPEN_PALM",
        "FIST",

        "THUMBS_UP",
        "THUMBS_DOWN",

        "SWIPE_RIGHT",
        "SWIPE_LEFT",

        "TWO_FINGERS",
        "THREE_FINGERS"
    }


    if gesture not in allowed:

        return jsonify({
            "ok": False,
            "error": "Invalid gesture"
        }), 400


    payload = {

        "gesture": gesture,

        "source": "dashboard",

        "timestamp": time.time()
    }


    mqtt_client.publish(
        COMMAND_TOPIC,
        json.dumps(payload),
        qos=0
    )


    return jsonify({
        "ok": True,
        "gesture": gesture
    })


if __name__ == "__main__":

    print(
        "AirSwitch dashboard:"
        " http://127.0.0.1:5000"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )