CONFIG = {
    "node_name": "pico-sdl-01",
    "profile": "picobricks",
    "runtime_version": "1.1.0",
    "protocol_version": "1.0.0",

    # Wi-Fi: leave blank to run USB-console-only until configured.
    "wifi": {
        "ssid": "",
        "password": "",
        "connect_timeout_s": 20,
        "hostname": "pico-sdl-01",
    },

    # SDL ASCII/TCP. Optional token is a trusted-LAN convenience, not strong security.
    "tcp": {
        "enabled": True,
        "port": 8765,
        "max_clients": 3,
        "auth_token": "",
    },

    # Human console over USB serial / REPL stdin.
    "console": {
        "enabled": True,
        "prompt": "SDL> ",
        "echo": False,
    },

    # Optional Nordic UART Service over BLE. Disabled by default for first bring-up.
    "ble": {
        "enabled": False,
        "name": "Pico-SDL",
    },

    # CRCL managed replaceable application.
    "crcl": {
        "active_path": "/apps/crcl_app.py",
        "backup_path": "/apps/crcl_app.py.bak",
        "stage_path": "/staging/crcl_app.py.part",
        "journal_path": "/staging/crcl_journal.json",
        "install_marker_path": "/staging/crcl_install.json",
        "previous_backup_path": "/apps/crcl_app.py.bak.previous",
        "recovery_failed_path": "/staging/crcl_app.py.recovery_failed",
        "max_bytes": 131072,
        "chunk_max_decoded": 384,
    },

    # Board profile. The PicoBricks values below are grounded in the project material:
    # RGB GP6, red LED GP7, button GP10, DHT GP11, relay GP12,
    # buzzer GP20, potentiometer GP26, LDR GP27, I2C GP4/GP5.
    "pins": {
        "i2c_id": 0,
        "i2c_sda": 4,
        "i2c_scl": 5,
        "i2c_freq": 400000,

        "picobricks_rgb": 6,
        "picobricks_red_led": 7,
        "picobricks_button": 10,
        "picobricks_dht": 11,
        "picobricks_relay": 12,
        "picobricks_buzzer": 20,
        "picobricks_pot_adc": 26,
        "picobricks_ldr_adc": 27,

        # Optional external sensors. Set to None until wired.
        "hcsr04_trig": None,
        "hcsr04_echo": None,
        "ds18b20_dq": None,
        "hx711_dout": None,
        "hx711_sck": None,
    },

    "devices": {
        "enable_picobricks": True,
        "enable_internal_temp": True,
        "enable_i2c_bus": True,
        "enable_mpu6050_autodetect": True,
        "enable_hcsr04": False,
        "enable_ds18b20": False,
        "enable_hx711": False,
    },

    # Optional load-cell calibration. raw_count_per_unit = counts per engineering unit.
    "hx711": {
        "offset": 0.0,
        "raw_count_per_unit": 1.0,
        "unit": "g",
        "gain_pulses": 1,
        "ready_timeout_ms": 800,
    },
}
