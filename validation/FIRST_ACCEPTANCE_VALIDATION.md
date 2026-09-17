# First Acceptance Validation Record

**Status:** NOT YET VALIDATED

This file becomes the dated evidence that the minimum SDL path has actually been reproduced from this repository. Do not change the status to PASS until the hardware path has been run.

## Test identity

- Date:
- Tester:
- Repository commit SHA:
- Clean checkout used: yes / no

## Hardware

- Arduino Uno or compatible:
- Multi-Function Shield (if fitted):
- DS18B20 sensor:
- DATA pin used:
- Pull-up resistor:
- USB interface/cable:

## Firmware environment

- Arduino IDE version:
- Board package/version:
- OneWire library/version:
- DallasTemperature library/version:

## Host environment

- Operating system:
- Python version:
- pyserial version:
- matplotlib version:
- Serial port:

## Procedure

- [ ] Clone or check out the tested commit.
- [ ] Wire the DS18B20 according to the endpoint source/header documentation.
- [ ] Build the endpoint firmware without errors.
- [ ] Upload the endpoint firmware.
- [ ] Confirm readable serial output at 115200 baud.
- [ ] Confirm at least one `TEMP_C,<value>` line.
- [ ] Install `bridge/requirements.txt` in a clean Python environment.
- [ ] Run `bridge/serial_logger.py` and create a CSV file.
- [ ] Confirm CSV contains host UTC timestamps and temperature values.
- [ ] Run `bridge/plot_csv.py` on the CSV file.
- [ ] Confirm a temperature-versus-time graph is displayed.
- [ ] Disconnect or miswire the sensor and confirm `ERROR,SENSOR` behavior, then restore it.

## Commands used

```text
python -m pip install -r bridge/requirements.txt
python bridge/serial_logger.py --port COM3 --seconds 60 --output validation/sample_run.csv
python bridge/plot_csv.py validation/sample_run.csv
```

Replace `COM3` with the actual serial port.

## Observed serial sample

```text
SDL,READY,DS18B20
TEMP_C,
```

## Observed result

Describe what happened, including deviations from the documented procedure.

## Outcome

- [ ] PASS — complete vertical slice reproduced from this repository.
- [ ] FAIL — record the failure below and keep repository readiness unchanged.

## Problems / deviations

Record compile errors, library conflicts, wiring corrections, serial-port issues, unexpected values, or documentation changes required.

## Promotion consequence

After a PASS, add the known-good sample output to `validation/`, update `ESTATE_STATUS.md`, and only then consider promoting the repository from `USABLE BUT INCOMPLETE` to `READY`.