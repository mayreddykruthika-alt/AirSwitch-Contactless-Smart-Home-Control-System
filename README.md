# AirSwitch-Contactless-Smart-Home-Control-System

AirSwitch is a contactless smart-home control demo. It recognizes hand gestures
from a webcam, sends commands over MQTT, and displays light and fan state in a
local web dashboard. The project includes a Python ESP32 simulator and an
optional ESP32/Wokwi firmware simulation.

## Requirements

- Python 3.10 or newer
- A webcam for gesture recognition
- PlatformIO (optional, for building the ESP32 firmware)

Install the Python dependencies from the project directory:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the demo

On Windows, run `run_all.bat` to launch the simulator, dashboard, and webcam
gesture detector. The dashboard is available at <http://127.0.0.1:5000>.

To run components individually, use separate terminals:

```powershell
python esp32_simulator.py
python server.py
python gesture_detector.py
```

The Python components and firmware use the public HiveMQ MQTT broker and the
`airswitch_es_demo_2026_v2` topic namespace. The demo requires an internet
connection for MQTT communication.

## ESP32 firmware

The Wokwi/PlatformIO project is in `wokwi/`. Build it from that directory with:

```powershell
pio run
```

Generated PlatformIO build files are local and are not part of the source
repository.