# SDL First Acceptance Quick Start

This is the shortest route through the reference implementation.

## 1. Hardware

Required:

- Arduino Uno or compatible.
- DS18B20 temperature sensor.
- 4.7 kOhm resistor.
- USB cable.
- Multi-Function Shield is optional for this acceptance path.

Wire the DS18B20 in normal powered mode:

| DS18B20 | Arduino Uno |
|---|---|
| VDD | 5V |
| GND | GND |
| DATA | D2 |

Place the **4.7 kOhm resistor between DATA and 5V**.

The canonical sketch is:

`endpoints/uno_ds18b20/uno_ds18b20.ino`

It requires the Arduino libraries **OneWire** and **DallasTemperature** and uses **115200 baud**.

## 2. Prove the host software before connecting hardware

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r bridge/requirements.txt
python bridge/serial_logger.py --input-file validation/fixtures/serial_sample.txt --output validation/software_check.csv
python bridge/plot_csv.py validation/software_check.csv --output validation/software_check.png
```

Expected logger result:

```text
SDL,READY,DS18B20
TEMP_C,23.625
TEMP_C,23.750
ERROR,SENSOR
TEMP_C,24.000
```

A CSV with three temperature rows and a PNG graph should be created.

## 3. Build and upload the endpoint

Open `endpoints/uno_ds18b20/uno_ds18b20.ino` in Arduino IDE.

Install:

- OneWire
- DallasTemperature

Select the Arduino Uno board and the correct serial port, then compile and upload.

Expected endpoint records include:

```text
SDL,READY,DS18B20
TEMP_C,23.625
```

If the sensor is absent or unreadable:

```text
ERROR,SENSOR
```

## 4. Run the real host path

Close Arduino Serial Monitor so the Python program can open the port.

On Windows, first identify the Uno COM port in Device Manager or Arduino IDE. Then run, for example:

```powershell
python bridge/serial_logger.py --port COM3 --seconds 60 --output validation/sample_run.csv
python bridge/plot_csv.py validation/sample_run.csv
```

Replace `COM3` with the actual port.

## 5. Record acceptance

Complete:

`validation/FIRST_ACCEPTANCE_VALIDATION.md`

Do not mark the repository `READY` merely because the software checks or automated compile checks pass. `READY` requires the physical DS18B20 -> Uno -> USB -> Python -> CSV -> graph path to be reproduced and recorded.
