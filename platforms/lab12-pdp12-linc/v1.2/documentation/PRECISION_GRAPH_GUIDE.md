# Precision Graph tab — LAB-12 v1.2

## Purpose and ownership

The **Precision graph** is the default Chrome operator display for the
PDP-12/LINC-inspired cooling experiment. It is a *display* rather than a
second experiment processor. It receives physical observations, run events,
and Newton-model coefficients from the Pico W over the existing USB Web Serial
link. The **Pico W still calculates the cooling constant, tau, RMS, event
times, and quality statistics**. JavaScript evaluates and draws the Pico's
published model for any graph X coordinate; it does **not independently fit**
model parameters.

## Features

- Full-size temperature-versus-**real elapsed experimental time** graph;
  measured temperatures are not plotted against sample index.
- Distinct **measured** (cyan), **Pico model** (gold), and **ambient** (dashed
  green) series, with purple vertical event markers and red × for invalid
  observations. Lines **break** at invalid readings or missing sequence IDs.
- Independent lower plot of temperature residuals from the Pico model; zero
  is shown as a dashed line. Residuals are presentation calculations using
  the Pico's coefficients and measurements, not a new scientific fit.
- Time windows: complete run, last 1, 5, 15, 30, or 60 minutes.
- Y-axis autoscale to actual visible values plus a modest margin, or manually
  specify °C minimum and maximum. The current range and tick interval are
  printed beneath the plot. Ticks use human-friendly steps.
- Mouse/pointer crosshair selecting the **nearest actual sample**, showing
  sequence number, time, measured temperature, model value, residual,
  reported quality, and clock source.
- **Hold view** freezes the horizontal time window without pausing the Pico,
  USB reception or CSV recording. Click **Resume follow** to track the
  advancing experiment again.
- **Save PNG** downloads the temperature plot image as shown. It does **not**
  save raw data; use **Data / CSV** for durable scientific evidence.
- An aligned side rail displays latest validated temperature, ambient,
  current Pico fit, run time, good/bad counts, sequence gaps, jitter, data
  source, and CSV status.

## How to use

1. Open `dashboard/lab12_dashboard.html` in **desktop Chrome**.
2. With no hardware connected, select **Lab guide → Start simulated
   experiment**. The graph is labelled **SYNTHETIC DEMO**.
3. For real measurements, connect the Pico W over USB in Chrome, configure
   acquisition under **Experiment control**, then switch to **Precision
   graph**. Close any serial console holding the Pico's USB port.
4. Start with **Last 5 min / Auto**, then select **Entire run** to compare
   early and late cooling. Hover over data points to inspect records.
5. Use **Data / CSV → Record to file** or **Download observations CSV**.
   A PNG or browser-memory graph alone is **not** a durable experimental record.

## Metrological cautions

- The DS18B20 provides 0.0625 °C output steps at 12-bit resolution; these
  steps do not establish ±0.0625 °C temperature accuracy.
- Pico event timestamps may represent the MSP430 completion pulse or UART
  reception and do not necessarily identify the exact instant at which the
  sensor measured water temperature.
- Graph autoscaling affects *appearance*, not instrument resolution. Manual
  ranges may deliberately clip observations; check displayed axis limits.
- The model uses a fixed ambient temperature entered by the operator. A
  changed ambient or the physical system's departure from exponential
  cooling can change the inferred constants and residuals.
- The prototype still requires real MSP430 and Pico hardware testing.

## Code tour (for students)

The single HTML file has a large, documented **Precision graph (V1.2)**
JavaScript section. Study it in this order:

1. `scopeBounds()` — maps selected time window onto elapsed seconds.
2. `scopeYBounds()` — derives real temperature or residual limits.
3. `tickStep()` — selects readable physical-axis divisions.
4. `scopePlot()` — draws grid, events, model and unmodified measurements.
5. `scopePointNear()` — chooses a real acquired record for crosshair display.
6. `scopeRefreshCards()` — organizes Pico telemetry around the graph.
7. `queueScopeRender()` — schedules browser rendering without changing the
   Pico acquisition or the CSV data pipeline.

`receive()` and `addSample()` remain the original USB protocol ingress and
logging path. The `msp430_new/` and `pico_w/` code is unchanged in v1.2.