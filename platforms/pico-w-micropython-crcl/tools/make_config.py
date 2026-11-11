#!/usr/bin/env python3
"""Create a config.json for the Pico W without editing Python source."""
import argparse, getpass, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["picobricks","sensor-rig"], default="picobricks")
    ap.add_argument("--output", default="config.json")
    ns = ap.parse_args()

    project = Path(__file__).resolve().parents[1]
    src = project / ("config.picobricks.example.json" if ns.profile == "picobricks"
                     else "config.sensor_rig.example.json")
    cfg = json.loads(src.read_text())

    node = input("Node name [%s]: " % cfg["node_name"]).strip()
    if node:
        cfg["node_name"] = node
        cfg["wifi"]["hostname"] = node

    cfg["wifi"]["ssid"] = input("Wi-Fi SSID: ").strip()
    cfg["wifi"]["password"] = getpass.getpass("Wi-Fi password: ")
    token = getpass.getpass("Optional SDL token (Enter for none): ")
    cfg["tcp"]["auth_token"] = token

    out = Path(ns.output)
    out.write_text(json.dumps(cfg, indent=2) + "\n")
    print("Wrote", out)
    print("Copy it to the Pico filesystem root as /config.json")

if __name__ == "__main__":
    main()
