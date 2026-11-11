# Bench Acceptance Sequence — v1.1

Do these in order. Do not debug Wi-Fi, BLE, CRCL, power-loss recovery, and external sensors simultaneously.

## M0 — USB resident-core proof

- [ ] MicroPython boots.
- [ ] Startup banner reports v1.1.0.
- [ ] `HELP` responds.
- [ ] `PING` responds.
- [ ] `DEV LIST` responds.
- [ ] `DEV READ pb.pot` produces a plausible changing value.
- [ ] `DEV READ pb.ldr` changes with light level.
- [ ] `DEV WRITE pb.led 1` and `0` visibly operate the LED.
- [ ] Note free filesystem space and free heap before further work.

## M1 — PicoBricks revision/environment proof

- [ ] `I2C SCAN` completes.
- [ ] If SHTC3 is present, address `0x70` appears and `pb.shtc3`/`pb.env` are listed.
- [ ] If no SHTC3 is present and the board uses DHT11, `pb.dht`/`pb.env` are listed.
- [ ] `DEV READ pb.env` returns plausible temperature/humidity.
- [ ] `temp1` maps to the detected environmental sensor unless DS18B20 is explicitly configured.

## M2 — I2C / IMU proof

- [ ] Expected board-local I2C devices appear.
- [ ] If an MPU-6050 is connected at `0x68`, `imu1` appears in `DEV LIST`.
- [ ] `DEV READ imu1` reports plausible acceleration/gyro values.

## M3 — Wi-Fi/TCP proof

- [ ] Pico prints a valid IP address.
- [ ] `python tools/acceptance.py <IP>` passes.
- [ ] TCP still works if the USB terminal is closed.
- [ ] USB console still works if Wi-Fi is unavailable.

## M4 — CRCL normal update proof

- [ ] `APP STATUS` reports the seed app.
- [ ] Push `examples/crcl_app_measure.py`.
- [ ] Target verifies length, CRC32, SHA-256, and syntax.
- [ ] New app reports healthy/running.
- [ ] `CRCL.ROLLBACK` restores the previous app.
- [ ] Interrupt one network transfer deliberately, reconnect with `--resume`, and complete it.

## M5 — CRCL abrupt-reset/power-loss proof

Perform these only after M4 is reliable. Keep USB recovery available.

- [ ] Reset during DATA transfer before a chunk starts; resume succeeds.
- [ ] Reset immediately after a DATA chunk appears to have been sent; `CRCL.STATUS` reports a coherent next sequence/offset and resume succeeds.
- [ ] Remove power during a DATA transfer; after reboot the stage is either committed through the last complete chunk or repaired to the previous committed prefix.
- [ ] Reset between candidate promotion and install commit; boot restores the prior known-good app.
- [ ] Repeat the above several times and inspect `.recovery_failed`/`.failed` artifacts when produced.

These tests qualify actual flash/filesystem behavior. Desktop simulations do not replace them.

## M6 — Failure proof

- [ ] Send an intentionally wrong CRC32; target rejects it.
- [ ] Upload a syntax-error app; target refuses `CRCL.END`.
- [ ] Upload an app whose `health()` returns False; installation rolls back.
- [ ] Upload an app whose `tick()` throws; resident command server remains alive and app stops after repeated errors.

## M7 — External sensors

Add one at a time:

1. DS18B20
2. HC-SR04 (with 5 V ECHO level reduction)
3. HX711
4. MPU-6050 / other I2C IMU

For every device, first establish electrical safety, then raw driver behavior, then logical-device behavior, then experiment behavior.

## M8 — BLE

Only after M0–M7 are stable:

- [ ] enable BLE in config;
- [ ] connect with a Nordic UART Service client;
- [ ] send `CMD 1 PING`;
- [ ] verify fragmented notifications reconstruct correctly;
- [ ] compare semantics with TCP;
- [ ] test disconnect/reconnect during read-only traffic before attempting CRCL over BLE.

BLE is an additional transport, not a second protocol.
