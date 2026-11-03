# Hardware Wiring & Electrical Bring-Up

## 3.3 V wiring, one external DS18B20

```text
DS18B20 (externally powered)
    VDD ------------------------------- MSP430 3.3 V
    GND -----+------------------------ MSP430 GND ---- Pico GND
    DQ ------+--(4.7 kΩ pull-up to 3.3 V)-- MSP430 P1.7

MSP430 G2553                            RP2040 Pico / Pico W
   P1.2 (TXD) -------------------------- GP1 (UART0 RX)
   P1.1 (RXD) <-------------------------- GP0 (UART0 TX)
   P2.0 (one pulse after capture) ------ GP2 (optional input)
   GND --------------------------------- GND

Pico USB ------------------------------- PC USB (Chrome Web Serial)
```

**Do not connect the boards' two 3.3 V output rails together.** Supply each
board through its normal supply connector/debug programmer. Share ground and
use only 3.3 V logic. Never feed 5 V UART into the Pico. Do not power the
DS18B20 parasite-style; this code assumes external VDD. The original source
uses `READ ROM (0x33)` and thus needs exactly **one device on the 1-Wire bus**.

## Physical verification sequence

1. Confirm your actual PCB's pinout, MCU orientation, voltages, ground and
   pull-up placement. Do not infer a physical header position from GPIO name.
2. Before connecting Pico UART, check MSP430 P1.2 TX idle HIGH around 3.3 V;
   verify with a scope if available. Connect common ground first.
3. Confirm 1-Wire reset presence pulse and each read/write slot on MSP430 P1.7
   with a logic analyzer. Review timing against the DS18B20 datasheet.
4. Flash MSP430 new cooling app. Observe `DEVICE,READY,COOLING_V1` on its UART
   using a suitable external 3.3 V serial interface **or** via Pico once ready.
5. Flash MicroPython Pico files, close Thonny, attach Chrome Web Serial, press
   STATUS, then send START. Verify readings include both validated ROM CRC and
   scratchpad CRC. Discard any `valid=false` samples.
6. Connect P2.0 -> GP2 only after confirming that P2.0 pulses HIGH (3.3 V) for
   approximately 1 ms after a conversion; verify marker_count increments.
7. Compare a stable temperature with an independent thermometer before
   running a cooling experiment. `85.0 C` can be a DS18B20 power-on default;
   don't accept it as proof of a fresh conversion without checking timing.

## Measurement interpretation

- `clock_source=gp2_soft_irq`: RP2040 timestamp of rising P2.0 GPIO; affected by
  MicroPython interrupt latency and scheduling; it is *end of acquisition*.
- `clock_source=uart_arrival`: fallback RP2040 timestamp of completed UART
  evidence; includes variable UART and software latency.
- `delta_ms`: interval between observed events, not certified ADC sample timing.
- This release does not implement PIO 1-Wire pulse-width measurement; it is a
  clearly identified extension, not a falsely claimed working subsystem.
