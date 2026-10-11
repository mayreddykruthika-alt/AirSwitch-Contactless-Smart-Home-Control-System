#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

// ============================================================
// AIRSWITCH - WOKWI SIMULATION
// ============================================================

// ---------------- WiFi ----------------

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// ---------------- MQTT ----------------

const char* MQTT_SERVER = "broker.hivemq.com";
const int MQTT_PORT = 1883;

const char* COMMAND_TOPIC =
    "airswitch_es_demo_2026_v2/command";

const char* STATUS_TOPIC =
    "airswitch_es_demo_2026_v2/status/wokwi";

// ============================================================
// HARDWARE
// ============================================================

// Smart light
const int LIGHT_PIN = 2;

// Stepper motor / fan
const int FAN_A_PLUS  = 16;
const int FAN_A_MINUS = 17;
const int FAN_B_PLUS  = 18;
const int FAN_B_MINUS = 19;

// ============================================================
// STATE
// ============================================================

bool lightOn = false;
int lightBrightness = 50;

bool fanOn = false;
int fanSpeed = 50;

String lastGesture = "NONE";

// ============================================================
// MQTT
// ============================================================

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ============================================================
// STEPPER
// ============================================================

int stepIndex = 0;

unsigned long lastStepTime = 0;

// Stepper sequence
const int stepSequence[4][4] = {
    {HIGH, LOW,  HIGH, LOW},
    {LOW,  HIGH, HIGH, LOW},
    {LOW,  HIGH, LOW,  HIGH},
    {HIGH, LOW,  LOW,  HIGH}
};


// ============================================================
// LIGHT
// ============================================================

void updateLight()
{
    if (!lightOn || lightBrightness <= 0)
    {
        digitalWrite(LIGHT_PIN, LOW);
    }
    else
    {
        // Reliable ON/OFF operation for Wokwi.
        digitalWrite(LIGHT_PIN, HIGH);
    }
}


// ============================================================
// STOP STEPPER
// ============================================================

void stopFan()
{
    digitalWrite(FAN_A_PLUS, LOW);
    digitalWrite(FAN_A_MINUS, LOW);
    digitalWrite(FAN_B_PLUS, LOW);
    digitalWrite(FAN_B_MINUS, LOW);
}


// ============================================================
// ONE STEPPER STEP
// ============================================================

void doStep()
{
    digitalWrite(
        FAN_A_PLUS,
        stepSequence[stepIndex][0]
    );

    digitalWrite(
        FAN_A_MINUS,
        stepSequence[stepIndex][1]
    );

    digitalWrite(
        FAN_B_PLUS,
        stepSequence[stepIndex][2]
    );

    digitalWrite(
        FAN_B_MINUS,
        stepSequence[stepIndex][3]
    );

    stepIndex++;

    if (stepIndex >= 4)
    {
        stepIndex = 0;
    }
}


// ============================================================
// FAN UPDATE
// ============================================================

void updateFan()
{
    if (!fanOn || fanSpeed <= 0)
    {
        stopFan();
    }
}


// ============================================================
// FAN SPEED INTERVAL
// ============================================================

unsigned long getStepInterval()
{
    if (fanSpeed <= 25)
    {
        return 80;
    }

    if (fanSpeed <= 50)
    {
        return 50;
    }

    if (fanSpeed <= 75)
    {
        return 30;
    }

    return 15;
}


// ============================================================
// RUN FAN
// ============================================================

void runFan()
{
    if (!fanOn || fanSpeed <= 0)
    {
        return;
    }

    unsigned long now = millis();

    unsigned long interval = getStepInterval();

    if (now - lastStepTime >= interval)
    {
        lastStepTime = now;

        doStep();
    }
}


// ============================================================
// SEND STATUS
// ============================================================

void publishStatus()
{
    char message[350];

    snprintf(
        message,
        sizeof(message),

        "{\"light\":{\"on\":%s,\"brightness\":%d},"
        "\"fan\":{\"on\":%s,\"speed\":%d},"
        "\"last_gesture\":\"%s\","
        "\"device\":\"Wokwi ESP32\"}",

        lightOn ? "true" : "false",
        lightBrightness,

        fanOn ? "true" : "false",
        fanSpeed,

        lastGesture.c_str()
    );

    mqttClient.publish(
        STATUS_TOPIC,
        message
    );

    Serial.println();
    Serial.println("Status sent:");
    Serial.println(message);
}


// ============================================================
// APPLY GESTURE
// ============================================================

void applyGesture(String gesture)
{
    gesture.trim();

    Serial.println();
    Serial.println("==============================");
    Serial.print("Parsed gesture: ");
    Serial.println(gesture);
    Serial.println("==============================");

    lastGesture = gesture;


    // --------------------------------------------------------
    // OPEN PALM
    // --------------------------------------------------------

    if (gesture == "OPEN_PALM")
    {
        lightOn = true;

        Serial.println("LIGHT: ON");

        updateLight();
    }


    // --------------------------------------------------------
    // FIST
    // --------------------------------------------------------

    else if (gesture == "FIST")
    {
        lightOn = false;

        Serial.println("LIGHT: OFF");

        updateLight();
    }


    // --------------------------------------------------------
    // THUMBS UP
    // --------------------------------------------------------

    else if (gesture == "THUMBS_UP")
    {
        lightOn = true;

        lightBrightness += 25;

        if (lightBrightness > 100)
        {
            lightBrightness = 100;
        }

        Serial.print("LIGHT BRIGHTNESS: ");
        Serial.print(lightBrightness);
        Serial.println("%");

        updateLight();
    }


    // --------------------------------------------------------
    // THUMBS DOWN
    // --------------------------------------------------------

    else if (gesture == "THUMBS_DOWN")
    {
        lightBrightness -= 25;

        if (lightBrightness < 0)
        {
            lightBrightness = 0;
        }

        if (lightBrightness == 0)
        {
            lightOn = false;
        }
        else
        {
            lightOn = true;
        }

        Serial.print("LIGHT BRIGHTNESS: ");
        Serial.print(lightBrightness);
        Serial.println("%");

        updateLight();
    }


    // --------------------------------------------------------
    // SWIPE RIGHT
    // --------------------------------------------------------

    else if (gesture == "SWIPE_RIGHT")
    {
        fanOn = true;

        Serial.println("FAN: ON");
        Serial.print("FAN SPEED: ");
        Serial.print(fanSpeed);
        Serial.println("%");

        updateFan();
    }


    // --------------------------------------------------------
    // SWIPE LEFT
    // --------------------------------------------------------

    else if (gesture == "SWIPE_LEFT")
    {
        fanOn = false;

        stopFan();

        Serial.println("FAN: OFF");
    }


    // --------------------------------------------------------
    // TWO FINGERS
    // --------------------------------------------------------

    else if (gesture == "TWO_FINGERS")
    {
        fanOn = true;

        fanSpeed += 25;

        if (fanSpeed > 100)
        {
            fanSpeed = 100;
        }

        Serial.print("FAN SPEED: ");
        Serial.print(fanSpeed);
        Serial.println("%");

        updateFan();
    }


    // --------------------------------------------------------
    // THREE FINGERS
    // --------------------------------------------------------

    else if (gesture == "THREE_FINGERS")
    {
        fanOn = true;

        fanSpeed -= 25;

        if (fanSpeed < 25)
        {
            fanSpeed = 25;
        }

        Serial.print("FAN SPEED: ");
        Serial.print(fanSpeed);
        Serial.println("%");

        updateFan();
    }


    // --------------------------------------------------------
    // UNKNOWN
    // --------------------------------------------------------

    else
    {
        Serial.println("Unknown gesture!");
    }


    publishStatus();
}


// ============================================================
// MQTT CALLBACK
// ============================================================

void mqttCallback(
    char* topic,
    byte* payload,
    unsigned int length
)
{
    String message = "";

    for (unsigned int i = 0; i < length; i++)
    {
        message += (char)payload[i];
    }

    Serial.println();
    Serial.println("MQTT message received:");
    Serial.println(message);


    // Find "gesture"
    int keyStart =
        message.indexOf("\"gesture\"");

    if (keyStart == -1)
    {
        Serial.println(
            "Gesture field not found."
        );

        return;
    }


    // Find :
    int colon =
        message.indexOf(":", keyStart);

    if (colon == -1)
    {
        Serial.println(
            "Invalid gesture message."
        );

        return;
    }


    // Find opening quote
    int valueStart =
        message.indexOf("\"", colon);

    if (valueStart == -1)
    {
        Serial.println(
            "Gesture value not found."
        );

        return;
    }

    valueStart++;


    // Find closing quote
    int valueEnd =
        message.indexOf("\"", valueStart);

    if (valueEnd == -1)
    {
        Serial.println(
            "Invalid gesture value."
        );

        return;
    }


    String gesture =
        message.substring(
            valueStart,
            valueEnd
        );

    gesture.trim();

    applyGesture(gesture);
}


// ============================================================
// WIFI CONNECTION
// ============================================================

void connectWiFi()
{
    Serial.println();
    Serial.println("Connecting to WiFi...");

    WiFi.begin(
        WIFI_SSID,
        WIFI_PASSWORD
    );

    while (
        WiFi.status() != WL_CONNECTED
    )
    {
        delay(500);

        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi connected!");

    Serial.print("IP address: ");

    Serial.println(
        WiFi.localIP()
    );
}


// ============================================================
// MQTT CONNECTION
// ============================================================

void connectMQTT()
{
    while (!mqttClient.connected())
    {
        Serial.println();
        Serial.println("Connecting to MQTT...");

        String clientID =
            "AirSwitch-Wokwi-";

        clientID +=
            String(
                random(
                    1000,
                    9999
                )
            );

        if (
            mqttClient.connect(
                clientID.c_str()
            )
        )
        {
            Serial.println(
                "MQTT connected!"
            );

            mqttClient.subscribe(
                COMMAND_TOPIC
            );

            Serial.println(
                "Subscribed to:"
            );

            Serial.println(
                COMMAND_TOPIC
            );

            publishStatus();
        }
        else
        {
            Serial.print(
                "MQTT connection failed. State = "
            );

            Serial.println(
                mqttClient.state()
            );

            delay(3000);
        }
    }
}


// ============================================================
// SETUP
// ============================================================

void setup()
{
    Serial.begin(115200);

    delay(1000);

    Serial.println();
    Serial.println("==============================");
    Serial.println("   AIRSWITCH WOKWI ESP32");
    Serial.println("==============================");


    // Light

    pinMode(
        LIGHT_PIN,
        OUTPUT
    );


    // Stepper

    pinMode(
        FAN_A_PLUS,
        OUTPUT
    );

    pinMode(
        FAN_A_MINUS,
        OUTPUT
    );

    pinMode(
        FAN_B_PLUS,
        OUTPUT
    );

    pinMode(
        FAN_B_MINUS,
        OUTPUT
    );


    // Initial state

    digitalWrite(
        LIGHT_PIN,
        LOW
    );

    stopFan();


    // WiFi

    connectWiFi();


    // MQTT

    mqttClient.setServer(
        MQTT_SERVER,
        MQTT_PORT
    );

    mqttClient.setCallback(
        mqttCallback
    );


    connectMQTT();
}


// ============================================================
// LOOP
// ============================================================

void loop()
{
    if (
        WiFi.status() != WL_CONNECTED
    )
    {
        connectWiFi();
    }


    if (
        !mqttClient.connected()
    )
    {
        connectMQTT();
    }


    mqttClient.loop();


    runFan();


    delay(1);
}