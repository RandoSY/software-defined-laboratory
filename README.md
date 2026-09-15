# Software-Defined Laboratory (SDL)

SDL is the central laboratory architecture of the Rando Young Intellectual Estate: a way to connect inexpensive physical experiments to software and AI without requiring expensive laboratory infrastructure.

## Core pattern

The minimum SDL path is intentionally simple:

**physical endpoint -> host bridge -> AI collaboration -> real measurement**

A useful SDL can begin with an Arduino Uno, Multi-Function Shield, and one sensor over USB serial. Richer reference systems may use Pico W, ESP32-class hardware, BLE, Wi-Fi, and browser interfaces.

## Canonical components

- **SDL** — the overall laboratory architecture.
- **SUPER** — the dedicated low-cost laboratory hardware family/reference bench computer.
- **MCP** — a higher-level interface layer for AI-assisted laboratory work where appropriate.
- **Host bridge** — connects simple device measurements to host software.
- **Protocols** — small, human-readable messages where practical.
- **Dashboards** — reusable interfaces for observation and control.
- **Reference experiments** — bounded physical experiments that prove the architecture end to end.

UNO/MFS, Pico W, micro:bit, ESP32, and similar boards are endpoint/reference tiers, not competing laboratory architectures.

## First acceptance path

The first outsider-verifiable release should demonstrate a cheap endpoint reading a real sensor, reliable transfer to a host, clear observation of the measurement, AI-assisted interpretation, and documentation that another person can follow.

A DS18B20 temperature experiment is a preferred baseline because the phenomenon, wiring, data, and failure modes are easy to inspect.

## Relationship to CORE 10

SDL supplies instrumentation and AI collaboration. CORE 10 supplies bounded educational investigations that give the infrastructure a reason to exist. One Cup Chemistry and energy experiments are important SDL demonstrations, while their curriculum home remains [core-10](https://github.com/RandoSY/core-10).

## Planned repository structure

- `docs/` — architecture, installation, protocols, acceptance tests
- `endpoints/` — endpoint firmware by reference tier
- `bridge/` — host bridge work
- `dashboard/` — reusable browser interfaces
- `examples/` — complete reference experiments
- `hardware/` — SUPER/reference hardware material when ready
- `validation/` — reproducibility evidence and known-good configurations

## Design rules

- Start at the cheapest useful rung.
- Do not require complexity when a simpler connection is sufficient.
- Add technology because it answers a real need.
- Keep messages and measurements inspectable.
- Separate endpoint behavior from host intelligence.
- Treat AI as a collaborator with the experiment, not a substitute for the experiment.
- Preserve a direct path so the physical measurement remains understandable.

## Current state

**Lifecycle:** `active`

**Priority:** P1 finishing work.

This repository currently establishes the canonical scope. Source and guides still need to be migrated and individually verified. Nothing here claims that a complete numbered SDL release has yet been reproduced from this repository.
