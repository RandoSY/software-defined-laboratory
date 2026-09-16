# SDL 8.0 — Unified Dynamic Code Distribution

**Recovery status:** concept/architecture recovered from the Intellectual Estate Library visual `SDL 8.0 Architecture Overview.png` on 16 September 2026.  
**Package evidence:** `evidence/SUPER_SDL_COMPLETE_v0.8.0.sha256.txt` records the checksum of a complete v0.8.0 ZIP that has not yet surfaced as a standalone Library file.

## Architectural idea

SDL 8.0 treats different embedded execution environments as adapters behind one stable device-management, discovery, and MCP-facing architecture. The host side should not require a different conceptual API simply because a target runs eForth, MicroBlocks SmallVM, or CircuitPython.

The recovered architecture is explicitly **one architecture, three tiers, multiple execution engines**.

## Stable upper layer

The diagram shows:

`Codex / LLM <-> MCP Bridge <-> SDL Windows Gateway v8.0`

The MCP bridge is marked **stable, generic interface — unchanged**.

The SDL Windows Gateway provides:

- device management;
- adapters;
- discovery;
- code deployment;
- YMP runtime transport;
- Traffic Cop functions.

The key design choice is that execution-engine differences are handled below the generic MCP surface.

## Three recovered execution tiers

### Tier 1 — Tiny: ATmega328P

- execution engine: **eForth**;
- program unit: Forth words / definitions;
- transport: serial, optionally through a BLE bridge;
- typical resources shown: about 32 KB flash / 2 KB RAM;
- role: small jobs, fast control, deterministic behavior.

### Tier 2 — Middle: nRF52833 / micro:bit v2

- execution engine: **MicroBlocks SmallVM**;
- program unit: live scripts / VM chunks;
- transport: BLE using a dual-channel model;
- programming channel: MicroBlocks IDE service;
- runtime channel: Nordic UART Service carrying YMP;
- typical resources shown: about 512 KB flash / 128 KB RAM;
- role: dynamic edge node, sensors, real-time and autonomous work.

### Tier 3 — Large: RP2040 / Pico W

- execution engine: **CircuitPython**;
- program unit: `.py` files / modules;
- transport: USB or Wi-Fi, with filesystem/TCP mechanisms;
- typical resources shown: about 2 MB flash / 264 KB RAM;
- role: high-level logic, networking, data processing, AI integration.

## Provisioning model

A target profile is meant to declare at least:

- node name;
- processor;
- execution engine;
- transport;
- deployment mechanism;
- runtime transport;
- capabilities.

The recovered example uses an nRF52833 node with MicroBlocks, BLE transport, MicroBlocks deployment, NUS runtime, and capabilities such as IMU, GPIO, ADC, I2C and PWM.

This makes the execution engine an explicit property of the node rather than an assumption hidden in host code.

## Generic MCP program surface

The recovered visual says the MCP program methods remain unchanged and lists a surface of this form:

- `device.discover`
- `device.info`
- `capability.list`
- `program.install(target, program)`
- `program.start(target)`
- `program.stop(target)`
- `program.remove(target)`
- `device.command(target, ...)`
- `device.read(target, ...)`
- `device.status(target)`

The important idea is not the exact spelling of every method. It is that the same administrative verbs survive while adapters translate those verbs into target-specific deployment operations.

## Example command flow

The recovered example is conceptually:

1. an AI/client requests a capability addition for a target;
2. MCP receives a generic `program.install(...)` operation;
3. SDL Gateway selects the target's MicroBlocks adapter;
4. the BLE programming channel installs VM chunks and starts the program;
5. the nRF52833 executes the program and retains it in flash;
6. normal sensor data and commands continue over YMP on NUS.

Programming and runtime communication are therefore intentionally separate channels.

## Recovered v8.0 changes

The architecture visual identifies these changes:

- MicroBlocks adapter added;
- execution-engine profiles added to provisioning;
- BLE deployment for nRF52833;
- generic `program.*` MCP methods retained;
- unified discovery and capability reporting;
- dual-channel BLE for programming plus runtime;
- no required Codex/MCP interface redesign;
- code deployment treated as an explicit administrative action.

## Why this matters

SDL 8.0 is a generalization of the Software-Defined Laboratory idea. A laboratory node is not defined by one language or one board. It is defined by discoverable capability plus an adapter that can install and run appropriate behavior on the execution engine available at that scale.

That allows tiny deterministic devices, medium dynamic edge nodes, and larger Python-capable laboratory computers to participate in one experimental fabric without forcing all hardware into the same runtime.

## Validation boundary

This file preserves the recovered architecture shown in the Library visual. It does **not** claim that every v8.0 adapter or deployment path has been independently bench-validated from source recovered in this repository.

The surviving checksum record proves that a package named `SUPER_SDL_COMPLETE_v0.8.0.zip` existed with SHA-256:

`9e4b8f77e98f7c7474c9228d11615c4376b7da14da7fdbe7d8eb6d46b97dbdf8`

Until that ZIP or equivalent exact source is recovered, treat this document as an architectural record plus package-existence evidence, not as a substitute for the missing release archive.
