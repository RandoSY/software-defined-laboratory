# LAB-12 Operator & Teacher's Guide

## Premise

The DEC LINC/PDP-12 was organized around experimental operations. Here the
MSP430 collects temperature measurements, the RP2040 conducts and analyzes
the experiment, and the Chrome page acts as the operator's display, archival
recorder and administrator. The experiment is Newton's Law of Cooling.

## Inquiry questions (CAP: Capture → Analyze → Publish)

- **Capture:** What is the raw evidence in the DS18B20 scratchpad? Why must
  source sequence, CRC and observed clock be preserved?
- **Analyze:** How rapidly is the water cooling, and when will it approach
  ambient? How do a wrong ambient estimate or timing jitter affect k?
- **Publish:** Can a second student reproduce the analysis with only the CSV,
  event log and run metadata?

## Student lab 0 — experiment in simulation

Open `dashboard/lab12_dashboard.html` in Chrome, select **Lab guide** and
start demo. The demo opens the dedicated **Precision graph**. Observe that the curve
is auto-scaled using actual elapsed seconds (not sample index). Select
**Entire run**, inspect the readout of an individual sample with the mouse,
and experiment with a manual temperature range. Explore model residuals,
export CSV, and inspect `DEMO_ONLY` quality records. The simulation is
explicitly not proof of a physical temperature measurement.

## Student lab 1 — show me the evidence

Use the real MSP430/DS18B20 after electrical checkout. Record the ROM,
9-byte scratchpad, signed x16 and both CRC results. Cause a deliberately bad
CRC through `FAULT=1` and verify that the Pico **rejects** the observation
instead of drawing an inaccurate temperature point. Return to `FAULT=0`.

## Student lab 2 — what is the clock measuring?

Start with 5 s samples. Run first with the P2.0 marker disconnected so the Pico
uses UART arrival time. Add the physical event marker, run again, and compare
observed interval mean and SD. Neither method measures DS18B20 internal
sampling instant; the marker reflects **end of completed transaction**.
Document the remaining error terms. Examine 16-bit sequence gaps after a
brief interruption. No claims of nanosecond-level resolution.

## Student lab 3 — Newton's cooling

Use a safe container of moderately warm water (avoid boiling water and
scalding). Insert a properly waterproofed DS18B20 probe and independently
measure ambient temperature. Record vessel, water volume, temperature, sensor
placement and whether the water was stirred. Begin a 5 s sampling run.

Newton's empirical first-order model:

```
T(t) = Ta + (T0 - Ta) exp(-k t)
          1
 tau = --------
          k
```

The Pico calculates k and tau by fitting
`ln(T - Ta) = intercept - k * t` for valid observations sufficiently above
ambient. It requires at least 6 valid observations and 5 s time span. It
reports RMS temperature residual, sample count and coefficients. The browser
only draws these values and computes plot coordinates from Pico coefficients.

Interpretations to explore:

- Compare still water and stirred water. Does a single exponential model
  remain appropriate?
- Add or remove a lid, press **Mark experiment event**, and see whether fit
  residuals increase after the perturbation.
- Arm a falling crossing at **40 °C**. The Pico independently raises and
  records the event on validated evidence; disconnect Chrome and reconnect
  after the crossing, then use **Retrieve Pico memory** to recover the event.
- Adjust the operator's ambient reference by ±2 °C. Compare fitted k, tau
  and residual RMS. Why is measuring ambient with another instrument useful?
- Change sample interval from 5 s to 10 s. Which information is lost, and
  which is unchanged?

## Student lab 4 — reproduce and communicate

Export raw observations CSV, event CSV and run metadata JSON. Keep them in one
folder. A peer should be able to re-derive the physical cooling curve,
identify invalid points, explain the model, and locate intervention events.
Save data **before closing Chrome**. Do not rely on Pico RAM for permanent logs.

## Teacher evaluation rubric

| Competency | Observable evidence |
|---|---|
| Hardware comprehension | Correct 3.3 V wiring, external pull-up and single sensor requirement |
| Acquisition | Explains One-Wire timing and conversion delay |
| Instrumentation | Distinguishes marker timestamp from sample instant |
| Validity | Independently checks CRCs and excludes injected faults |
| Numerical reasoning | Explains k, tau, ambient assumption and residual RMS |
| Publication | Shares CSV with raw evidence, time, notes and interventions |
| Architecture | Correctly separates MSP430, Pico and Chrome responsibilities |

## Safety and scientific honesty

DS18B20 calibration, waterproofing, self-heating and thermal coupling are not
proved by working CRCs. A timestamp may be precise in representation but
inaccurate in event provenance. Live UI graphics are a display, not a
measurement standard. The code is educational; no heater or hazardous load
may be controlled by the illustrative thermostat outputs.

## Student lab 5 — graphing as an instrument

Use the **Precision graph** tab (see `PRECISION_GRAPH_GUIDE.md`). Compare
the same run at a five-minute window and full-run scale. Note why a different
axis span changes the *appearance* of a residual without changing the actual
sensor data. Hold the graph window, continue acquiring, and verify that
CSV rows still increase. Mark an intervention and retrieve its time from
the graph and events CSV. Export the PNG *and* data CSV; explain why only the
CSV supports independent reanalysis.
