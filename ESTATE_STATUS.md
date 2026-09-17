# Estate Status — Software-Defined Laboratory

**Repository role:** Reference-standard repository for the Rando Young Intellectual Estate.

**Current status:** `USABLE BUT INCOMPLETE`

The repository now contains a coherent canonical SDL description, repository-local source for the first acceptance path, a host-side software preflight, automated host tests, an automated Uno compile check, and a formal physical validation record.

It is **not yet marked `READY`** because the complete physical DS18B20 -> Uno -> USB -> Python -> CSV -> graph path has not been re-run from a clean checkout and recorded by a human tester.

## Readiness vocabulary

### READY

A new reader can understand the project, obtain the required hardware/software, follow one documented path, and reproduce at least one meaningful physical result from the repository. Current source is clearly separated from historical material. Tested configurations and limitations are stated.

### USABLE BUT INCOMPLETE

The project is intelligible and useful, but at least one critical reproducibility condition has not yet been physically verified.

### ARCHIVAL

The repository preserves historically or intellectually valuable material but does not claim to provide a current reproducible implementation.

## SDL acceptance target

SDL becomes `READY` when an outsider can reproduce this minimum path:

1. DS18B20 makes a real temperature measurement.
2. Arduino Uno-class endpoint emits a human-readable record.
3. USB serial carries the record to the host.
4. Repository-local Python receives and records it.
5. The CSV is plotted.
6. The run begins from a clean checkout.
7. The exact tested configuration and commit are recorded.

## Present now

- Canonical SDL scope and design rules in `README.md`.
- Windows-friendly first path in `docs/QUICKSTART.md`.
- Arduino Uno + DS18B20 endpoint in `endpoints/uno_ds18b20/`.
- Human-readable `TEMP_C,<value>` protocol.
- Python host logger in `bridge/serial_logger.py`.
- CSV plotter in `bridge/plot_csv.py`.
- Hardware-independent serial fixture in `validation/fixtures/`.
- Unit tests in `tests/`.
- GitHub Actions checks for host software and Arduino Uno compilation.
- Physical acceptance procedure and record in `validation/FIRST_ACCEPTANCE_VALIDATION.md`.
- Preserved architecture, lineage, source snapshots, archive, and evidence material.

## Remaining gate

One gate remains before promotion to `READY`:

> Run the documented physical acceptance path on real hardware from a clean checkout and complete `validation/FIRST_ACCEPTANCE_VALIDATION.md`.

Automated tests and compilation are evidence that the repository is internally coherent. They are **not** a substitute for observing a real sensor through the complete path.

Until that physical gate is passed, this file is the authoritative readiness statement.
