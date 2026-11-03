# LAB-12 Operator Protocol and Evidence Contract

The **MSP430 UART0 ↔ Pico UART0** hop is 9600 baud, 8N1, 3.3 V logic.
Chrome ↔ Pico USB MicroPython CDC/REPL is serial framing but **115200 baud in
Web Serial is a nominal setting**, not the physical USB line rate.

## MSP430 original-compatible evidence

Example fields (example only; replace with actual CRC-correct hardware bytes):

```text
SEQ_HEX=0001,STATUS=0,STATE=1,X16_HEX=02D0,ROM=...,SCRATCH=...,INJECT=0
```

Each actual observation is a single ASCII line, terminated by CRLF. Original
modules are used to build the ROM/scratchpad evidence. Pico independently
checks both CRCs and agreement between the reported x16 temperature and raw
scratchpad decoding. If invalid, `temp_c` becomes null and that observation is
never included in the scientific fit. The unmodified raw line is also saved.

## USB console commands — single line, plain ASCII

| Command | Owner | Effect |
|---|---|---|
| `HELLO` / `STATUS` | Pico | Return lab state, fit, buffer and acquisition clock statistics |
| `HISTORY` | Pico | Replay up to 160 RAM observations plus event marks |
| `CLEAR` | Pico | New run, resets RAM/model/events; does not erase browser CSV |
| `AMBIENT=23.0` | Pico | Set fixed ambient for Newton's cooling model |
| `FIT=1` / `FIT=0` | Pico | Enable/disable on-board cooling fit |
| `TRIGGER=40` | Pico | Autonomously mark downward crossing of valid temperature through 40 °C |
| `TRIGGER=OFF` | Pico | Disarm threshold condition |
| `MARK=STIRRED` | Pico | Timestamp human event in resident RAM, then publish it |
| `START` / `STOP` | MSP430, forwarded by Pico | Physical acquisition request |
| `RATE=5000` | MSP430, forwarded by Pico | Target nominal acquisition interval, 1000..60000 ms |
| `PING` | MSP430, forwarded by Pico | Verify subordinate responds |
| `FAULT=0` / `1` / `2` | MSP430 | No fault / instructional corrupted CRC / absent evidence |

The command sets are intentionally **whitelisted**. No Python execution or
arbitrary machine commands are accepted over the operator USB port.

## Pico → Chrome USB messages

One compact **JSON object per line**. Main `type` categories:

- `hello`: identifies Pico LAB-12 runtime.
- `status`: current run, period, valid/invalid/lost counts, model, clock stats,
  and threshold trigger state.
- `sample`: original sensor evidence (raw UART line and bytes) plus validated
  temperature, observed experiment time, quality and Pico model.
- `event`: physical crossing or operator-added experiment marker.
- `history_start`, `history_sample`, `history_end`: replay when requested.
- `parameter`: changed ambient, fit state, rate or trigger setting.
- `cleared`, `command_sent`, `msp_message`, `error`: diagnostic/admin messages.

The browser ignores non-JSON startup banners printed by the MicroPython REPL.

## Data reliability details

- Sequence arithmetic accounts for MSP430 16-bit wrap. Duplicate/old
  observations are flagged and excluded from fitting.
- Full Pico experiment memory is 160 latest observations; no guarantee that
  a disconnected browser receives any point that already aged out of memory.
- When reconnecting, click **Retrieve Pico memory**; duplicate sequence IDs are
  suppressed in the current browser run.
- CSV raw UART evidence remains a field of each observation. Run notes are in
  separately exported metadata JSON. Events are exported to their own CSV.
- Pico model fit uses the latest valid points in its RAM; already exported CSV
  `model_c` and `residual_c` reflect fit values **at the time of arrival**.
  The plotted curve always uses the Pico's most recent fit coefficients.