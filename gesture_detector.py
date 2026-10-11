import cv2
import mediapipe as mp
import paho.mqtt.client as mqtt
import json
import time
import math


# ============================================================
# AIRSWITCH CONFIGURATION
# ============================================================

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPIC = "airswitch_es_demo_2026_v2/command"

CAMERA_INDEX = 0

COOLDOWN_SECONDS = 1.0

SWIPE_THRESHOLD = 0.20


# ============================================================
# MEDIAPIPE
# ============================================================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


# ============================================================
# DISTANCE FUNCTION
# ============================================================

def distance(a, b):
    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2 +
        (a.z - b.z) ** 2
    )


# ============================================================
# FINGER DETECTION
# ============================================================

def get_finger_states(lm):

    # Index
    index_extended = (
        lm[8].y < lm[6].y - 0.025
    )

    # Middle
    middle_extended = (
        lm[12].y < lm[10].y - 0.025
    )

    # Ring
    ring_extended = (
        lm[16].y < lm[14].y - 0.025
    )

    # Pinky
    pinky_extended = (
        lm[20].y < lm[18].y - 0.025
    )

    return (
        index_extended,
        middle_extended,
        ring_extended,
        pinky_extended
    )


# ============================================================
# THUMBS UP
# ============================================================

def is_thumbs_up(lm):

    index, middle, ring, pinky = get_finger_states(lm)

    # All four fingers must be closed
    other_fingers_closed = not any([
        index,
        middle,
        ring,
        pinky
    ])

    if not other_fingers_closed:
        return False

    # Thumb must point upward
    thumb_tip = lm[4]
    thumb_ip = lm[3]
    thumb_mcp = lm[2]

    thumb_up = (
        thumb_tip.y < thumb_ip.y - 0.01
        and
        thumb_tip.y < thumb_mcp.y - 0.01
    )

    return thumb_up


# ============================================================
# THUMBS DOWN
# ============================================================

def is_thumbs_down(lm):

    index, middle, ring, pinky = get_finger_states(lm)

    # All four fingers must be closed
    other_fingers_closed = not any([
        index,
        middle,
        ring,
        pinky
    ])

    if not other_fingers_closed:
        return False

    # Thumb must point downward
    thumb_tip = lm[4]
    thumb_ip = lm[3]
    thumb_mcp = lm[2]

    thumb_down = (
        thumb_tip.y > thumb_ip.y + 0.01
        and
        thumb_tip.y > thumb_mcp.y + 0.01
    )

    return thumb_down


# ============================================================
# FIST
# ============================================================

def is_fist(lm):

    index, middle, ring, pinky = get_finger_states(lm)

    extended_count = sum([
        index,
        middle,
        ring,
        pinky
    ])

    # If any main finger is extended,
    # it is NOT a normal fist.
    if extended_count != 0:
        return False

    # Extra check: fingertips should be close
    # to the wrist/palm.

    wrist = lm[0]

    fingertips = [
        lm[8],
        lm[12],
        lm[16],
        lm[20]
    ]

    curled_fingers = 0

    for tip in fingertips:

        if distance(tip, wrist) < 0.32:
            curled_fingers += 1

    return curled_fingers >= 3


# ============================================================
# OPEN PALM
# ============================================================

def is_open_palm(lm):

    fingers = get_finger_states(lm)

    return all(fingers)


# ============================================================
# TWO FINGERS
# ============================================================

def is_two_fingers(lm):

    index, middle, ring, pinky = get_finger_states(lm)

    return (
        index
        and
        middle
        and
        not ring
        and
        not pinky
    )


# ============================================================
# THREE FINGERS
# ============================================================

def is_three_fingers(lm):

    index, middle, ring, pinky = get_finger_states(lm)

    return (
        index
        and
        middle
        and
        ring
        and
        not pinky
    )


# ============================================================
# STATIC GESTURE CLASSIFIER
# ============================================================

def classify_static(lm):

    # IMPORTANT:
    # Check THUMBS UP and THUMBS DOWN
    # BEFORE checking FIST.
    #
    # This prevents 👍 / 👎 from being
    # incorrectly classified as FIST.

    if is_thumbs_up(lm):
        return "THUMBS_UP"

    if is_thumbs_down(lm):
        return "THUMBS_DOWN"

    # FIST
    if is_fist(lm):
        return "FIST"

    # OPEN PALM
    if is_open_palm(lm):
        return "OPEN_PALM"

    # TWO FINGERS
    if is_two_fingers(lm):
        return "TWO_FINGERS"

    # THREE FINGERS
    if is_three_fingers(lm):
        return "THREE_FINGERS"

    return "UNKNOWN"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 55)
    print("        AIRSWITCH HAND GESTURE DETECTOR")
    print("=" * 55)
    print()

    # --------------------------------------------------------
    # MQTT
    # --------------------------------------------------------

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"airswitch-camera-{int(time.time())}"
    )

    print(
        f"Connecting to MQTT: "
        f"{MQTT_BROKER}:{MQTT_PORT}"
    )

    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60
    )

    client.loop_start()

    print("MQTT connected.")
    print()

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not cap.isOpened():

        print(
            "ERROR: Camera could not be opened."
        )

        print(
            "Try changing CAMERA_INDEX = 0 "
            "to CAMERA_INDEX = 1."
        )

        return

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    last_sent_gesture = ""

    last_sent_time = 0

    wrist_history = []

    # --------------------------------------------------------
    # MEDIAPIPE
    # --------------------------------------------------------

    with mp_hands.Hands(

        static_image_mode=False,

        max_num_hands=1,

        min_detection_confidence=0.65,

        min_tracking_confidence=0.60,

        model_complexity=0

    ) as hands:

        while True:

            success, frame = cap.read()

            if not success:

                print(
                    "Camera frame error."
                )

                break

            # Mirror image
            frame = cv2.flip(
                frame,
                1
            )

            # BGR → RGB
            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            result = hands.process(
                rgb
            )

            gesture = "NO HAND"

            # ------------------------------------------------
            # HAND FOUND
            # ------------------------------------------------

            if result.multi_hand_landmarks:

                hand = result.multi_hand_landmarks[0]

                lm = hand.landmark

                # Draw hand skeleton
                mp_draw.draw_landmarks(
                    frame,
                    hand,
                    mp_hands.HAND_CONNECTIONS
                )

                # --------------------------------------------
                # SWIPE TRACKING
                # --------------------------------------------

                wrist_history.append(
                    lm[0].x
                )

                wrist_history = (
                    wrist_history[-8:]
                )

                if len(wrist_history) >= 6:

                    dx = (
                        wrist_history[-1]
                        -
                        wrist_history[0]
                    )

                    # RIGHT SWIPE
                    if dx > SWIPE_THRESHOLD:

                        gesture = "SWIPE_RIGHT"

                        wrist_history.clear()

                    # LEFT SWIPE
                    elif dx < -SWIPE_THRESHOLD:

                        gesture = "SWIPE_LEFT"

                        wrist_history.clear()

                    else:

                        gesture = classify_static(lm)

                else:

                    gesture = classify_static(lm)

            # ------------------------------------------------
            # SEND MQTT COMMAND
            # ------------------------------------------------

            now = time.time()

            if (
                gesture
                not in (
                    "NO HAND",
                    "UNKNOWN"
                )
                and
                (
                    gesture != last_sent_gesture
                    or
                    now - last_sent_time
                    >= COOLDOWN_SECONDS
                )
            ):

                payload = {
                    "gesture": gesture,
                    "source": "camera",
                    "timestamp": now
                }

                client.publish(
                    MQTT_TOPIC,
                    json.dumps(payload),
                    qos=0
                )

                print(
                    f"Gesture sent: {gesture}"
                )

                last_sent_gesture = gesture

                last_sent_time = now

            # ------------------------------------------------
            # UI OVERLAY
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (10, 10),
                (520, 150),
                (15, 20, 30),
                -1
            )

            cv2.putText(
                frame,
                f"Gesture: {gesture}",
                (25, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Last: {last_sent_gesture or '-'}",
                (25, 78),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (150, 220, 255),
                2
            )

            cv2.putText(
                frame,
                "OPEN PALM = Light ON",
                (25, 108),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (170, 255, 190),
                1
            )

            cv2.putText(
                frame,
                "FIST = Light OFF",
                (270, 108),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (255, 180, 180),
                1
            )

            cv2.putText(
                frame,
                "THUMBS UP/DOWN = Brightness",
                (25, 135),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 220, 150),
                1
            )

            cv2.imshow(
                "AirSwitch - Hand Gesture Recognition",
                frame
            )

            # Q = quit
            if (
                cv2.waitKey(1)
                &
                0xFF
                ==
                ord("q")
            ):

                break

    # --------------------------------------------------------
    # CLEANUP
    # --------------------------------------------------------

    cap.release()

    cv2.destroyAllWindows()

    client.loop_stop()

    client.disconnect()


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":
    main()