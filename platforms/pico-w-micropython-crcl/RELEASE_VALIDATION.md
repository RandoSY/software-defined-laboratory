# RELEASE VALIDATION — Pico W SDL/CRCL Reference Node v1.1.0

Release status: **software release candidate validated; physical Pico W/PicoBricks M0 acceptance pending.**

## Automated checks run in the build environment

- PASS: `tests/test_protocol.py`
- PASS: `tests/test_crcl.py`
  - staged transfer
  - CRC32 verification
  - SHA-256 verification
  - successful install
  - rollback
  - bad checksum rejection
  - syntax-error rejection
  - failed `health()` rollback
- PASS: `tests/test_crcl_powerloss.py`
  - full pending DATA append recovered as committed
  - partial pending DATA append repaired to prior committed prefix
  - corruption of newest journal slot falls back to older valid slot
  - reset after candidate promotion rolls back to known-good active app
  - reset before promotion preserves old active app and staged candidate
- PASS: `tests/test_shtc3.py`
  - wake/measure command sequence
  - SHTC3 CRC-8 validation
  - temperature/humidity conversion
- PASS: `tests/test_capabilities.py`
  - manifest validation
  - transactional registration
  - capability invocation
- PASS: CPython `compileall` across repository source.

## v1.1 recovery invariants

1. Incoming CRCL bytes go only to staging.
2. DATA sequence numbers are strict and monotonic.
3. The two-slot journal preserves one older valid state while writing the next state.
4. Each DATA append has a persisted pending record before bytes are appended.
5. Reboot recovery distinguishes no append, complete append, and partial append.
6. Declared byte count is enforced.
7. CRC32 is mandatory; SHA-256 is supported and used by the supplied uploader.
8. Python syntax is compiled before promotion.
9. An install marker is persisted before active application mutation.
10. The previous active application is preserved through candidate health checking.
11. An install interrupted before commit is conservatively rolled back at next boot when a known-good predecessor exists.
12. The host never silently retries an uncertain CRCL DATA transaction; it resumes from target-reported state.

## Scope boundary

This package has not been physically executed on the user's Pico W/PicoBricks during this build pass. In particular, desktop simulations do not prove the behavior of RP2040 flash/LittleFS under an actual abrupt power cut.

Physical acceptance is defined in `docs/ACCEPTANCE.md`.

## Release contents

Target board files live under `board_files/`.
Host administration tools live under `tools/`.
Regression tests live under `tests/`.
Reference documentation lives under `docs/`.

## Deliberately not claimed in v1.1

- hostile-code sandboxing;
- encrypted/authenticated production-grade remote-code execution;
- automatic wireless deployment of complete multi-file capability packages;
- physically validated BLE CRCL transfer;
- completed M0 hardware qualification.
