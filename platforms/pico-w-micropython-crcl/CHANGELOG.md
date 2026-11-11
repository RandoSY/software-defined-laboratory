# Changelog

## v1.1.0 — recovery hardening and PicoBricks revision support

This is a quality/hardening release of the v1.0 software release candidate. It does not claim completion of physical M0 bench acceptance.

### CRCL durability

- Replaced the single transfer journal with a two-slot, CRC-protected journal.
- Added a durable pending-chunk record before every DATA append.
- On reboot, a fully written pending chunk is verified and committed automatically.
- A partially written pending chunk is discarded back to the last committed byte prefix.
- Preserved the explicit `--resume` model: uncertain physical or network operations are not silently repeated.
- Added staged-file length reconciliation against committed journal state.

### Application promotion safety

- Added an install transaction marker written before active application promotion.
- A reset/power loss before commit now causes conservative rollback to the pre-install application on the next boot.
- A promoted but uncommitted candidate is preserved for diagnosis rather than trusted automatically.
- Preserves an older rollback generation until the new candidate has passed `health()` and the transaction commits.

### PicoBricks

- Added SHTC3 support on I2C address `0x70` for newer PicoBricks revisions.
- Added DHT11/SHTC3 auto-selection: SHTC3 is preferred when detected and validated; otherwise DHT11 is used.
- Added stable `pb.env` device role while retaining `pb.dht` on older hardware and exposing `pb.shtc3` on newer hardware.
- `temp1` now binds to the detected PicoBricks environmental sensor when a DS18B20 is not explicitly configured.

### Tests

- Added reset/power-loss simulation for full and partial in-flight CRCL DATA chunks.
- Added dual-slot journal corruption recovery test.
- Added interrupted application promotion rollback tests.
- Added SHTC3 protocol/CRC/conversion test.
- Existing protocol, CRCL, and capability-registry tests remain passing.

## v1.0.0

Initial Pico W SDL/CRCL reference-node software release candidate.
