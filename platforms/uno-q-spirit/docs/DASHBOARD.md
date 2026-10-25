# UNO Q Spirit Experiment Dashboard

For operator workflows, architecture, safety notes, and the wider lab roadmap, see the [User's & Programmer's Guide](USER_AND_PROGRAMMERS_GUIDE.pdf).

**Status:** Running on the UNO Q Linux side at `http://192.168.0.165:7000` (UNO Q LAN address `192.168.0.165`, TCP port `7000`).

## Architecture

The STM32 sketch remains responsible for sensor access and acquisition. The Linux dashboard service polls the existing `spirit.status` Bridge RPC, timestamps each snapshot on the MPU, manages experiment runs, persists samples in SQLite, and serves the user interface and CSV downloads to a browser. The browser communicates with Linux over HTTP; it does not access the MCU Bridge directly.

The dashboard uses the project logo with a dark navy/slate surface, cyan/teal highlights, and pastel sensor accents. Its tabs separate **Monitor** (live values and trend), **Experiments** (run setup and controls), and **Archive** (saved runs and CSV exports). Start, stop, refresh, and navigation controls give visible operator feedback and have keyboard-accessible tabs. It does not change the firmware mode or control sensor acquisition. It records the mode reported by the MCU. In synthetic mode, the interface marks the source as simulation and stores the `SYNTH` sensor states in each CSV row.

## Start and access

The dashboard is installed as the `uno-q-spirit-dashboard.service` systemd service on the UNO Q. It starts at boot, runs as `arduino` with access to the `arduino-router` group, and restarts automatically if the process exits with an error. The Arduino Router service and Arduino App CLI daemon are also enabled at boot.

Check or restart the dashboard with:

```bash
sudo systemctl status uno-q-spirit-dashboard.service
sudo systemctl restart uno-q-spirit-dashboard.service
```

Follow its log with `sudo journalctl -u uno-q-spirit-dashboard.service -f`. Check the health endpoint with `curl http://127.0.0.1:7000/healthz`.

The unit file is `/etc/systemd/system/uno-q-spirit-dashboard.service`. Its effective configuration is:

```ini
[Unit]
Description=UNO Q Spirit experiment dashboard
After=network-online.target arduino-router.service
Wants=network-online.target

[Service]
Type=simple
User=arduino
SupplementaryGroups=arduino-router
WorkingDirectory=/home/arduino/UNO_Q_Spirit_v0.1.1_reviewed
Environment=SPIRIT_DASHBOARD_HOST=0.0.0.0
Environment=SPIRIT_DASHBOARD_PORT=7000
ExecStart=/home/arduino/.venvs/uno-q-spirit/bin/python /home/arduino/UNO_Q_Spirit_v0.1.1_reviewed/python/dashboard_server.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

To enable it after reinstalling the unit, run `sudo systemctl daemon-reload` and `sudo systemctl enable --now uno-q-spirit-dashboard.service`.

For a one-off foreground run while debugging, from the project directory use:

```bash
cd /home/arduino/UNO_Q_Spirit_v0.1.1_reviewed
source /home/arduino/.venvs/uno-q-spirit/bin/activate
python python/dashboard_server.py
```

Open `http://192.168.0.165:7000` in Chrome on the same network. The server binds to `0.0.0.0` by default. Override the host or port with `SPIRIT_DASHBOARD_HOST` and `SPIRIT_DASHBOARD_PORT` if needed.

## Experiments and files

Enter an experiment name, a recording interval from 1 to 3,600 seconds, and optional notes. Start and stop apply to Linux-side recording only. Runs are retained in:

```text
~/.local/share/uno-q-spirit/experiments.sqlite3
```

The recent-experiments table provides a per-run CSV download. CSV rows include UTC timestamp, MCU mode/profile, sensor states and values, the explicit HX711 calibrated flag, AS7343 gain and all 18 raw readout slots, and the MCU loop tick count. Spectral slots are raw counts, not wavelength-calibrated measurements.

## HTTP endpoints

- `GET /` — dashboard page
- `GET /api/state` — latest telemetry, Bridge health, recent chart history and active run
- `GET /api/runs` — recent run metadata and sample counts
- `POST /api/runs` — start recording; JSON body: `name`, `interval_s`, optional `notes`
- `POST /api/runs/stop` — stop the active recording
- `GET /api/runs/<run-id>/csv` — download one run
- `GET /healthz` — Bridge connection health (`200` when connected, `503` otherwise)

## Validation and access notes

Validated on the UNO Q at `192.168.0.165`: HTTP 200 for the dashboard page, stylesheet, script, and project logo; `/healthz` returned `{"ok":true,"bridge_ok":true}`. A separate temporary smoke run exercised start/stop, SQLite recording, and CSV download and captured three synthetic samples.

The current server uses plain HTTP and has no login; it is intended for a trusted local network. The systemd service starts on boot and restarts after a process failure. A board reboot itself was not performed as part of this service setup; boot persistence is configured through the enabled `multi-user.target` unit.

## Accessibility

Use the **Text size** selector in the header to choose Default, Larger (110%), or Largest (120%). The choice is saved in this browser and restored on the next visit.


## Screenshot

The README includes a current capture of the Monitor tab at [`docs/images/dashboard-monitor.png`](images/dashboard-monitor.png). It shows connected synthetic telemetry for interface illustration; displayed values are not physical sensor measurements.
