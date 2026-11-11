# PicoBricks Quick Start — v1.1

The supplied profile uses the documented PicoBricks GPIO map:

| Function | GPIO |
|---|---:|
| I2C SDA | GP4 |
| I2C SCL | GP5 |
| RGB LED | GP6 |
| Red LED | GP7 |
| Button | GP10 |
| Older-board DHT11 | GP11 |
| Relay | GP12 |
| Buzzer | GP20 |
| Potentiometer | GP26 / ADC0 |
| LDR | GP27 / ADC1 |

Newer PicoBricks revisions may use SHTC3 temperature/humidity on the I2C bus at address `0x70` instead of DHT11. v1.1 detects and validates SHTC3 first, then falls back to DHT11.

Motor control hardware remains intentionally outside the resident v1.1 lab surface.

## First commands

```text
DEV LIST
DEV READ pb.button
DEV READ pb.pot
DEV READ pb.ldr
DEV WRITE pb.led 1
DEV WRITE pb.led 0
DEV WRITE pb.rgb 20,0,80
DEV WRITE pb.buzzer 1000,100
DEV READ pb.env
DEV READ temp1
I2C SCAN
```

Expected environment-device naming:

```text
newer SHTC3 board: pb.env + pb.shtc3
older DHT11 board: pb.env + pb.dht
```

`temp1` points to the detected environment sensor unless an explicitly configured DS18B20 already owns that stable role.

## Zero-additional-wiring demo

A PicoBricks can demonstrate the SDL architecture without external sensors:

- button = digital input
- red LED = digital output
- RGB LED = richer output
- potentiometer = analog input
- LDR = analog input
- DHT11 or SHTC3 = environmental measurement, depending on revision
- buzzer = timed output
- I2C scan = bus discovery
- CRCL application = replaceable behavior

That is enough for first acceptance before adding HC-SR04, DS18B20, HX711, or an IMU.
