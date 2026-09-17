# Software-Defined Laboratory (SDL)

**SDL is the central laboratory architecture of the Rando Young Intellectual Estate:** a way to connect inexpensive physical experiments to software and AI without requiring expensive laboratory infrastructure.

> **Estate status:** `USABLE BUT INCOMPLETE`  
> The first reference implementation is now repository-local and automatically checked. The remaining readiness gate is a recorded physical end-to-end run on real hardware.

See [ESTATE_STATUS.md](ESTATE_STATUS.md) for the exact readiness definition.

## Start here

If you want to run something rather than study the history:

1. **[Quick Start](docs/QUICKSTART.md)** — shortest Windows-friendly route through the first implementation.
2. **[First Acceptance Path](docs/FIRST_ACCEPTANCE_PATH.md)** — acceptance criteria and rationale.
3. **[First Acceptance Validation](validation/FIRST_ACCEPTANCE_VALIDATION.md)** — the physical test record that must pass before `READY`.
4. **[Project History](PROJECT_HISTORY.md)** — how SUPER, historical prototypes, and SDL fit together.
5. **[Repository Standard](docs/REPOSITORY_STANDARD.md)** — the template this repository establishes for the wider estate.

## The core pattern

The minimum SDL path is intentionally simple:

**physical endpoint -> transport -> host bridge -> observation/recording -> AI collaboration where useful -> real measurement**

A useful SDL can begin with an Arduino Uno, Multi-Function Shield, and one sensor over USB serial. Richer reference systems may use Pico W, ESP32-class hardware, micro:bit, BLE, Wi-Fi, browser interfaces, MCP, and dynamically deployed code.

Advanced capabilities are extensions of the same pattern, not prerequisites for proving it.

## First reference implementation

The first outsider-verifiable SDL path is:

**DS18B20 -> Arduino Uno / Multi-Function Shield tier -> USB serial -> Python host bridge -> CSV -> graph**

Repository-local implementation:

- `endpoints/uno_ds18b20/uno_ds18b20.ino` — endpoint firmware.
- `bridge/protocol.py` — protocol parsing and validation.
- `bridge/serial_logger.py` — USB serial or fixture input to CSV.
- `bridge/plot_csv.py` — interactive or PNG graph output.
- `validation/fixtures/serial_sample.txt` — known-good software fixture.
- `tests/test_bridge.py` — host protocol/logging tests.
- `.github/workflows/reference-standard.yml` — automated host checks and Arduino Uno compilation.

Before connecting hardware, the fixture can be passed through the same logger:

```powershell
python -m pip install -r bridge/requirements.txt
python bridge/serial_logger.py --input-file validation/fixtures/serial_sample.txt --output validation/software_check.csv
python bridge/plot_csv.py validation/software_check.csv --output validation/software_check.png
```

The physical validation procedure is in [docs/QUICKSTART.md](docs/QUICKSTART.md).

## Human-readable protocol

The baseline endpoint intentionally says very little:

```text
SDL,READY,DS18B20
TEMP_C,23.625
ERROR,SENSOR
```

This is a deliberate design choice. Extra metadata should be added only when it solves an actual need.

## Canonical components

- **SDL** — the overall laboratory architecture.
- **SUPER** — a dedicated low-cost laboratory hardware/reference implementation family within SDL.
- **MCP** — a higher-level interface layer for AI-assisted laboratory work where appropriate.
- **Endpoint** — sensing, actuation, timing, and simple local behavior.
- **Transport** — USB serial, BLE UART, Wi-Fi/TCP, or another inspectable link.
- **Host bridge** — connects endpoint messages to host-side software.
- **Protocols** — short, human-readable messages where practical.
- **Dashboards** — reusable observation and control interfaces.
- **Reference experiments** — bounded physical experiments proving the architecture end to end.
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

```text
endpoints/        current endpoint firmware
bridge/           current host-side bridge and plotting software
tests/            automated software tests
validation/       fixtures and physical validation records
docs/             current operating and estate documentation
architecture/     preserved architecture documents
source-snapshots/ pinned historical source repositories
lineage/          historical lineage material
archive/          research/reconstruction material
evidence/         preserved integrity/validation artifacts
```

Historical code is not treated as current merely because it is reachable through a source snapshot.

## Relationship to CORE 10

SDL supplies instrumentation and AI collaboration. CORE 10 supplies bounded educational investigations that give the infrastructure a reason to exist. One Cup Chemistry and energy experiments are important SDL demonstrations, while their curriculum home remains [core-10](https://github.com/RandoSY/core-10).

## What “finished” means here

A major technical repository is not estate-ready merely because files were copied into GitHub. It should have a clear front door, one reproducible golden path, repository-local source, explicit requirements, known expected output, dated validation evidence, project history, and a clear separation of current and archival material.

The full standard is in [docs/REPOSITORY_STANDARD.md](docs/REPOSITORY_STANDARD.md).

## Current state

**Lifecycle:** `active`  
**Priority:** P1 finishing work  
**Estate readiness:** `USABLE BUT INCOMPLETE`

The software and compile-verification infrastructure for the first vertical slice is now present. Promotion to `READY` is intentionally withheld until the documented physical sensor path is run and recorded.
