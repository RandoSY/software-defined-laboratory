# Project History — Software-Defined Laboratory

This file records the design lineage of SDL so that historical material is not mistaken for the current canonical architecture.

## Purpose of the history

The Intellectual Estate preserves old work, but preservation is not the same as endorsement. Earlier names, architectures, and packages remain useful evidence of how the system evolved. The current repository front page and current acceptance path take precedence when older material conflicts with them.

## Lineage

### Earlier laboratory-system work

The work developed through multiple low-cost physical-computing and AI-assisted laboratory experiments. Several names and implementation families appear in the historical record, including SUPER, DEXIS Lab, cloud/GSA prototypes, MCP-oriented work, browser dashboards, traffic-cop monitoring, and multiple microcontroller endpoint families.

### SUPER

SUPER became the dedicated low-cost laboratory hardware/reference-bench-computer family within the larger idea. Historical SUPER packages and guides are preserved because they contain implementation work and design rationale, but SUPER is not the name of the complete architecture.

### SDL consolidation

Software-Defined Laboratory (SDL) became the canonical umbrella architecture. The defining separation is:

- physical endpoint: sensing, actuation, timing, simple local behavior;
- transport: USB serial, BLE UART, Wi-Fi/TCP, or another inspectable link;
- host bridge: translates between the endpoint and host-side software;
- observation/control: dashboards, logging, analysis, and experiment interfaces;
- AI collaboration: interpretation, coding assistance, experiment variation, model checking, and higher-level orchestration where useful.

The minimum implementation intentionally begins below the sophisticated tiers: an inexpensive endpoint, one real sensor, USB serial, and a host program.

### 2026 reference-repository reconstruction

The GitHub estate migration preserved important architecture documents and historical snapshots, but preservation alone did not create a reproducible project. This reconstruction therefore separates three concerns:

1. **Canonical current path** — what a new reader should build first.
2. **Validated implementation** — material actually re-run from the repository.
3. **Archive and lineage** — prior packages, concepts, and evidence retained for research and reconstruction.

## Canonical design decisions

- SDL is the umbrella architecture.
- SUPER is a hardware/reference implementation family within SDL.
- The lowest useful tier should remain inexpensive and understandable.
- Arduino Uno + Multi-Function Shield is a valid entry tier; richer endpoints include Pico W, ESP32-class boards, micro:bit, and related devices.
- USB serial is the preferred initial bring-up transport when it is sufficient.
- BLE and Wi-Fi are capabilities, not requirements for the minimum path.
- Endpoint behavior should remain separable from host intelligence.
- Human-readable, short protocol messages are preferred where practical.
- The Traffic Cop is observational; closing it must not stop the laboratory from functioning.
- AI should collaborate with the physical experiment rather than replace it.
- The first outsider-verifiable path should be small enough to reproduce and inspect completely.

## Historical-source rule

Material in `archive/`, `lineage/`, and `source-snapshots/` is preserved evidence. It may contain valuable code and ideas, but it is not automatically current. When historical content is promoted into the current implementation, it should be copied or adapted into the canonical source tree, documented, and re-validated.

## Current reconstruction goal

The immediate goal is not to recover every historical SDL feature. It is to establish one complete, reproducible vertical slice and use the resulting repository structure as the reference standard for the rest of the Intellectual Estate.