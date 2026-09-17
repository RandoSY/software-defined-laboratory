# Software-Defined Laboratory (SDL)

**SDL is the central laboratory architecture of the Rando Young Intellectual Estate:** a way to connect inexpensive physical experiments to software and AI without requiring expensive laboratory infrastructure.

> **Estate status:** `USABLE BUT INCOMPLETE`  
> This repository is being reconstructed as the reference standard for the rest of the Intellectual Estate. It contains canonical architecture and preserved historical material, but it does not yet claim a freshly reproduced end-to-end release.

See [ESTATE_STATUS.md](ESTATE_STATUS.md) for the exact readiness definition and remaining work.

## Start here

If you are new to SDL, read these in order:

1. **This README** — what SDL is and why it exists.
2. **[First Acceptance Path](docs/FIRST_ACCEPTANCE_PATH.md)** — the smallest end-to-end implementation that will establish reproducibility.
3. **[Project History](PROJECT_HISTORY.md)** — how SUPER, historical prototypes, and SDL fit together.
4. **[Repository Standard](docs/REPOSITORY_STANDARD.md)** — the standard this repository is intended to establish for the wider estate.

## The core pattern

The minimum SDL path is intentionally simple:

**physical endpoint -> transport -> host bridge -> observation/recording -> AI collaboration where useful -> real measurement**

A useful SDL can begin with an Arduino Uno, Multi-Function Shield, and one sensor over USB serial. Richer reference systems may use Pico W, ESP32-class hardware, micro:bit, BLE, Wi-Fi, browser interfaces, MCP, and dynamically deployed code.

The advanced capabilities are extensions of the same pattern, not prerequisites for proving it.

## First reproducible target

The first outsider-verifiable SDL path is deliberately modest:

**DS18B20 -> Arduino Uno / Multi-Function Shield tier -> USB serial -> Python host bridge -> recorded temperature data -> simple graph**

This path becomes the first acceptance test because every layer is inspectable and inexpensive. It must be reproducible from a clean checkout before this repository is marked `READY`.

The detailed acceptance criteria are in [docs/FIRST_ACCEPTANCE_PATH.md](docs/FIRST_ACCEPTANCE_PATH.md).

## Canonical components

- **SDL** — the overall laboratory architecture.
- **SUPER** — a dedicated low-cost laboratory hardware/reference implementation family within SDL.
- **MCP** — a higher-level interface layer for AI-assisted laboratory work where appropriate.
- **Endpoint** — performs sensing, actuation, timing, and simple local behavior.
- **Transport** — USB serial, BLE UART, Wi-Fi/TCP, or another inspectable link.
- **Host bridge** — connects endpoint messages to host-side software.
- **Protocols** — short, human-readable messages where practical.
- **Dashboards** — reusable interfaces for observation and control.
- **Reference experiments** — bounded physical experiments that prove the architecture end to end.
- **AI collaboration** — interpretation, coding assistance, experiment variation, model checking, and orchestration where it adds value.

UNO/MFS, Pico W, micro:bit, ESP32, and similar boards are endpoint/reference tiers, not competing laboratory architectures.

## Design rules

- Start at the cheapest useful rung.
- Do not require complexity when a simpler connection is sufficient.
- Add technology because it answers a real need.
- Keep messages and measurements inspectable.
- Separate endpoint behavior from host intelligence.
- Prefer human-readable protocols where practical.
- Treat AI as a collaborator with the experiment, not a substitute for the experiment.
- Preserve a direct path so the physical measurement remains understandable.
- Keep observational tools such as the Traffic Cop nonessential to basic operation.
- Distinguish **tested**, **implemented**, **planned**, and **historical** material.

## Repository map

Current preserved material includes:

- `architecture/` — preserved architecture documents and diagrams.
- `source-snapshots/` — pinned historical source repositories used as reconstruction evidence.
- `lineage/` — historical lineage material.
- `archive/` — material preserved for research or reconstruction rather than presented as current.
- `evidence/` — preserved integrity/validation artifacts.
- `docs/` — current reconstruction and acceptance documentation.

As the first acceptance path is rebuilt, current implementation material should live directly in this repository under clear current-source directories such as:

```text
endpoints/
bridge/
examples/
validation/
hardware/        # when applicable
```

Historical code should not be treated as current merely because it is reachable through a submodule.

## Relationship to CORE 10

SDL supplies instrumentation and AI collaboration. CORE 10 supplies bounded educational investigations that give the infrastructure a reason to exist. One Cup Chemistry and energy experiments are important SDL demonstrations, while their curriculum home remains [core-10](https://github.com/RandoSY/core-10).

## What “finished” means here

This repository is intended to become the model for the rest of the Intellectual Estate. A major technical repository is not estate-ready merely because files have been copied into GitHub. It should have:

- a clear front door;
- one reproducible golden path;
- repository-local source needed for that path;
- explicit requirements and expected output;
- dated validation evidence;
- project history and canonical design decisions;
- clear separation of current, experimental, and archival material.

The full standard is in [docs/REPOSITORY_STANDARD.md](docs/REPOSITORY_STANDARD.md).

## Current state

**Lifecycle:** `active`  
**Priority:** P1 finishing work  
**Estate readiness:** `USABLE BUT INCOMPLETE`

The immediate reconstruction objective is not to recover every historical SDL feature. It is to make one small vertical slice completely reproducible, validate it, and then use this repository as the structural template for the other major repositories in the Intellectual Estate.