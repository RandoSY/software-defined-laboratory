# Third-party and platform references

This release intentionally prefers established platform facilities and published implementations before custom low-level code.

- MicroPython RP2 quick reference / Pico W networking:
  https://docs.micropython.org/en/latest/rp2/quickref.html
- MicroPython `machine.time_pulse_us`:
  https://docs.micropython.org/en/latest/library/machine.html
- MicroPython 1-Wire / DS18B20 example:
  https://docs.micropython.org/en/latest/esp8266/tutorial/onewire.html
- MicroPython Bluetooth API:
  https://docs.micropython.org/en/latest/library/bluetooth.html
- MicroPython `binascii.crc32`:
  https://docs.micropython.org/en/latest/library/binascii.html
- Robert Hammelrath `hx711` MicroPython repository:
  https://github.com/robert-hh/hx711
  The HX711 driver is an independent compact implementation informed by the same important timing practice: keep PD_SCK high pulses short and protected from interrupt latency.
- PicoBricks project material:
  https://picobricks.com/

No third-party source file is bundled wholesale in this package.

- PicoBricks revision support in v1.1 was cross-checked against previously archived PicoBricks/MicroBlocks material showing SHTC3 at I2C address 0x70 on newer boards and DHT11 on older boards.
