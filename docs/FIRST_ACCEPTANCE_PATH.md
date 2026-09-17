# SDL First Acceptance Path

The first SDL acceptance path is deliberately narrow. Its purpose is to prove the architecture end to end before restoring advanced features.

## Target

Produce a real temperature measurement with an inexpensive microcontroller endpoint, send it to a host using USB serial, record it with a small host program, and display or graph the result.

Preferred baseline:

**DS18B20 -> Arduino Uno / Multi-Function Shield tier -> USB serial -> Python host bridge -> recorded temperature data -> simple graph**

## Why this path

- inexpensive hardware;
- physically meaningful measurement;
- slow enough that timing is not difficult;
- easy to inspect with ordinary tools;
- serial transport is understandable and widely available;
- the same pattern can later be moved to Pico, ESP32, BLE, Wi-Fi, dashboards, and AI-assisted workflows.

## Required deliverables before acceptance

### Endpoint

- source code in the repository;
- explicit board/toolchain requirement;
- explicit sensor wiring;
- one simple human-readable serial message format;
- a clear startup indication;
- defined behavior for missing or invalid sensor data.

### Host

- repository-local Python program;
- minimal dependency list;
- serial-port selection instructions;
- console display of incoming values;
- CSV or similarly inspectable log output;
- simple plotting path.

### Protocol

The initial protocol should remain intentionally small. A suitable shape is:

```text
TEMP_C,23.625
```

Optional later fields such as timestamp, device ID, sequence number, or status should be added only when needed and documented before use.

### Validation

The acceptance record must state:

- date;
- endpoint board;
- sensor;
- firmware/toolchain version;
- host operating system;
- Python version;
- commit SHA tested;
- observed sample output;
- whether a clean checkout was used;
- any problems encountered.

## Acceptance test

A new reader should be able to:

1. Clone the repository.
2. Open the endpoint project using the documented toolchain.
3. Wire the DS18B20 from the repository instructions.
4. Build and upload the firmware.
5. Observe valid temperature messages over USB serial.
6. Run the host bridge.
7. Observe the same measurements at the host.
8. Produce a local log.
9. Plot a short run.
10. Compare the observed output with the documented known-good example.

Passing this test establishes the first complete SDL vertical slice.

## What this test does not attempt

The first acceptance path does not require BLE, Wi-Fi, MCP, cloud services, automatic code deployment, the Traffic Cop, multiple devices, advanced dashboards, or AI orchestration. Those are legitimate SDL capabilities, but none should block proof of the basic architecture.

## Promotion rule

Historical code may be used to implement this path, but it is not considered canonical merely because it exists in a source snapshot. Any promoted code must be placed in the current repository tree, documented, and tested through this procedure.