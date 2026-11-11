# Architecture

```text
                         PC / AI / Browser / Terminal
                                  |
          +-----------------------+----------------------+
          |                       |                      |
       USB console             Wi-Fi/TCP             BLE NUS
          |                    :8765                  optional
          +-----------------------+----------------------+
                                  |
                          Transport-independent
                          SDL ASCII command core
                                  |
             +--------------------+--------------------+
             |                    |                    |
        Device Registry     Capability Registry     CRCL Manager
             |                    |                    |
             |                    |              stage / verify /
             |                    |              promote / rollback
             |                    |                    |
             +-------------+------+--------------------+
                           |
                       App Manager
                     apps/crcl_app.py
                           |
          +----------------+-----------------------------+
          |         |        |       |        |          |
         I2C      GPIO      ADC    1-Wire   HX711    pulse timing
          |                            |                 |
         IMU                        DS18B20           HC-SR04
```

The permanent runtime carries infrastructure. Experimental meaning is late-bound.

## Stable device roles

The registry supplies logical identities. Current examples include:

- `pb.button`
- `pb.led`
- `pb.relay`
- `pb.rgb`
- `pb.buzzer`
- `pb.pot`
- `pb.ldr`
- `pb.dht`
- `temp1`
- `cpu_temp`
- `i2c0`
- `imu1`
- `distance1`
- `mass1`

A role appears only when its backend is available. `temp1` prefers a configured DS18B20 and otherwise uses the detected PicoBricks environmental sensor (SHTC3 on newer revisions or DHT11 on older revisions) when available. RP2040 CPU temperature remains separately named because it is not an ambient-temperature substitute.

## Runtime loop

The resident loop intentionally stays cooperative:

1. poll each transport;
2. parse complete lines;
3. dispatch one SDL request;
4. send response;
5. call one application `tick()`;
6. sleep briefly;
7. repeat.

Application code must therefore avoid long blocking loops. Timing-critical sensor operations belong in drivers, PIO, IRQ-backed implementations, or carefully bounded calls.

## Failure boundaries

- A lost TCP client does not stop the Pico runtime.
- Wi-Fi failure does not stop USB console access.
- Optional BLE failure does not stop TCP or console.
- Capability registration is private until validation completes.
- CRCL data writes only to staging.
- A verified app is backed up before promotion.
- Failed activation restores the previous app.
- Repeated app `tick()` exceptions stop the app, not the resident server.

## Security boundary

This is a trusted-bench architecture. The optional token is plaintext on the LAN. CRCL-delivered Python executes with interpreter privilege. It is not a sandbox.

Keep it on a trusted network for this development phase.
