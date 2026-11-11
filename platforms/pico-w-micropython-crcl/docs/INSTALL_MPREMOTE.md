# Install with mpremote

`mpremote` is the official MicroPython host-side remote-control tool.

Install it on the host:

```bash
python -m pip install --upgrade mpremote
```

With the Pico W connected over USB and MicroPython already installed:

```bash
cd board_files
mpremote cp boot.py :
mpremote cp main.py :
mpremote cp config_default.py :
mpremote cp -r sdl :
mpremote cp -r drivers :
mpremote cp -r capabilities :
mpremote cp -r apps :
mpremote cp -r staging :
```

Create your host-side `config.json`:

```bash
cd ..
python tools/make_config.py --profile picobricks
```

Copy it:

```bash
mpremote cp config.json :
```

Then reset and enter the REPL/console:

```bash
mpremote reset
mpremote repl
```

For iterative development, `mpremote mount` is also useful, but the acceptance milestone should run from files actually stored on the Pico.
