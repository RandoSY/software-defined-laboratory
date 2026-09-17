# First Acceptance Validation Record

**Status:** NOT YET PHYSICALLY VALIDATED

This file is the dated evidence that the minimum SDL path has actually been reproduced from this repository. Automated software and compile checks are useful preflight evidence; they do not replace this physical test.

## Automated preflight

The repository contains automated checks for:

- protocol parsing and malformed-input handling;
- fixture -> CSV logging;
- fixture -> headless plot generation;
- Arduino Uno compilation with OneWire and DallasTemperature.

A green automated run means the code is internally consistent on the CI environment. It does **not** mean a real DS18B20 has been observed.

## Test identity

- Date:
- Tester:
- Repository commit SHA:
- Clean checkout used: yes / no

## Hardware

- Arduino Uno or compatible:
- Multi-Function Shield (if fitted):
- DS18B20 sensor:
- DATA pin used: D2 unless changed
- Pull-up resistor: 4.7 kOhm DATA -> 5V
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
- [ ] Complete the fixture preflight in `docs/QUICKSTART.md`.
- [ ] Wire the DS18B20 according to the endpoint documentation.
- [ ] Build the endpoint firmware without errors.
- [ ] Upload the endpoint firmware.
- [ ] Confirm readable serial output at 115200 baud.
- [ ] Confirm at least one `TEMP_C,<value>` line.
- [ ] Run `bridge/serial_logger.py` and create a CSV file.
- [ ] Confirm CSV contains host UTC timestamps and temperature values.
- [ ] Run `bridge/plot_csv.py` on the CSV file.
- [ ] Confirm a temperature-versus-time graph is displayed.
- [ ] Disconnect or miswire the sensor and confirm `ERROR,SENSOR`, then restore it.

## Commands used

```powershell
python -m pip install -r bridge/requirements.txt
python bridge/serial_logger.py --port COM3 --seconds 60 --output validation/sample_run.csv
python bridge/plot_csv.py validation/sample_run.csv
```

Replace `COM3` with the actual serial port.

## Expected serial shape

```text
SDL,READY,DS18B20
TEMP_C,23.625
TEMP_C,23.750
```

A missing/unreadable sensor should produce:

```text
ERROR,SENSOR
```

## Observed serial sample

Paste several real lines here:

```text

```

## Observed result

Describe what happened, including deviations from the documented procedure.

## Outcome

- [ ] PASS — complete physical vertical slice reproduced from this repository.
- [ ] FAIL — record the failure below and keep repository readiness unchanged.

## Problems / deviations

Record compile errors, library conflicts, wiring corrections, serial-port issues, unexpected values, or documentation changes required.

## Promotion consequence

After a physical PASS, commit the completed record and a short known-good sample output. Only then promote `ESTATE_STATUS.md` from `USABLE BUT INCOMPLETE` to `READY`.
