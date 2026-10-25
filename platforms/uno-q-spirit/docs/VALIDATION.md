# Validation evidence — 2026-10-25

**Executed locally in isolated development environment, not on the user's UNO Q.**

| Check | Outcome | Evidence/limits |
|---|---|---|
| Python `unittest discover` | PASS | 12 named tests, including missing mock sensors, malformed response, invalid gain, CSV and bridge timeouts |
| C++ standard-library filter assertions | PASS | Signed 24-bit edges, echo conversion, invalid values, running moments, intervals; `g++ -std=c++17 -Wall -Wextra -Werror` |
| Arduino sketch built with **host C++ mock headers** | PASS | Sketch syntax under stubbed Arduino, Zephyr kernel and Adafruit interfaces; simulated absent sensors and mode commands |
| Synthetic host CLI | PASS | JSON sample and CSV capture in mock transport |
| Arduino UNO Q native board-core compile | NOT RUN | `arduino-cli` unavailable in validation container; missing board package and SDK |
| Physical STM32 U585 execution | NOT RUN | No remote terminal/hardware execution available |
| Electrical safety test of original AVR Spirit PCB | NOT RUN | Original physical schematic/PCB not furnished; source PDF explicitly 5 V-only |
| Sensor accuracy / spectral fidelity | NOT RUN | Must characterize with actual sensor module, controlled lighting, standards and scope |
| End-to-end Arduino Bridge | NOT RUN | Stubbed in host harness only |

## Reproduction

```bash
python3 -m unittest discover -s tests -v
c++ -std=c++17 -Wall -Wextra -Werror tests/cpp/test_filters.cpp -o /tmp/spirit_filters && /tmp/spirit_filters
c++ -std=c++17 -Wall -Wextra -Werror -Itests/stubs -x c++ tests/cpp/test_sketch.cpp -o /tmp/spirit_sketch && /tmp/spirit_sketch
python3 python/spirit_cli.py --mock status
```

No hardware function is certified. This is **a software engineering preview with disciplined validation boundaries**.
