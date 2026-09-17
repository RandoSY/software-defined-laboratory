# Estate Status — Software-Defined Laboratory

**Repository role:** Reference-standard repository for the Rando Young Intellectual Estate.

**Current status:** `USABLE BUT INCOMPLETE`

The repository contains a coherent canonical description of SDL, preserved architecture material, and pinned historical source snapshots. It does **not yet** contain a fully reproduced, outsider-verifiable end-to-end release built from the repository alone.

## Readiness vocabulary

The Intellectual Estate uses three repository-readiness states:

### READY
A new reader can understand the project, obtain the required hardware/software, follow one documented path, and reproduce at least one meaningful result from the repository. Current source is clearly separated from historical material. Tested configurations and limitations are stated.

### USABLE BUT INCOMPLETE
The project is intelligible and contains useful material, but at least one critical reproducibility element is missing or has not been re-verified: source, installation steps, hardware details, test evidence, or a complete runnable example.

### ARCHIVAL
The repository preserves historically or intellectually valuable material but does not claim to provide a current reproducible implementation.

## SDL acceptance target

SDL becomes `READY` when an outsider can reproduce this minimum path:

1. Inexpensive physical endpoint.
2. Real sensor measurement.
3. Human-readable transport to a host.
4. Host software receives and records the measurement.
5. The measurement is observable in a simple display or graph.
6. The same path is documented from hardware connection through result.
7. The procedure has been re-run from a clean checkout and the tested date/configuration recorded.

The preferred first acceptance experiment is a DS18B20 temperature measurement using the low-cost Arduino Uno / Multi-Function Shield tier and USB serial host transport.

## What is present now

- Canonical SDL scope and design rules in `README.md`.
- Preserved architecture documents in `architecture/`.
- Historical lineage and archive material.
- Pinned source snapshots in `source-snapshots/`.
- A preserved checksum record in `evidence/`.

## What is still required

- A repository-local endpoint implementation for the minimum acceptance path.
- A repository-local host bridge for that path.
- A complete wiring/setup guide.
- A known-good sample data file.
- A repeatable acceptance test.
- A dated validation record showing the path was actually reproduced.

Until those items are complete, this file is the authoritative statement of readiness.