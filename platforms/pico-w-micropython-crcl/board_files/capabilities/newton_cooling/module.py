import math
try:
    import utime as time
except ImportError:
    import time

_state = {
    "running": False,
    "mode": "model",
    "t0_ms": 0,
    "initial_c": 80.0,
    "ambient_c": 22.0,
    "tau_s": 180.0,
    "sensor_id": "temp1",
    "samples": 0,
}

def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time()*1000)

def _ticks_diff(a,b):
    return time.ticks_diff(a,b) if hasattr(time, "ticks_diff") else a-b

def register(registry, lab):
    def start(args):
        _state["mode"] = str(args.get("MODE", "model")).lower()
        _state["initial_c"] = float(args.get("INITIAL_C", 80.0))
        _state["ambient_c"] = float(args.get("AMBIENT_C", 22.0))
        _state["tau_s"] = max(0.001, float(args.get("TAU_S", 180.0)))
        _state["sensor_id"] = str(args.get("SENSOR", "temp1"))
        if _state["mode"] == "sensor" and not lab.devices.has(_state["sensor_id"]):
            raise ValueError("sensor mode requires device %s" % _state["sensor_id"])
        _state["t0_ms"] = _ticks_ms()
        _state["samples"] = 0
        _state["running"] = True
        return status({})

    def sample(args):
        if not _state["running"]:
            raise ValueError("cooling run not started")
        elapsed_s = _ticks_diff(_ticks_ms(), _state["t0_ms"]) / 1000.0
        if _state["mode"] == "sensor":
            data = lab.devices.read(_state["sensor_id"])
            temp = float(data.get("temperature_c", data.get("value")))
            source = _state["sensor_id"]
        else:
            temp = _state["ambient_c"] + (_state["initial_c"]-_state["ambient_c"]) * math.exp(-elapsed_s/_state["tau_s"])
            source = "model"
        _state["samples"] += 1
        return {
            "name":"cooling_sample",
            "elapsed_s":elapsed_s,
            "temperature_c":temp,
            "source":source,
            "sample":_state["samples"],
        }

    def status(args):
        return {
            "name":"cooling_status",
            "running":int(_state["running"]),
            "mode":_state["mode"],
            "samples":_state["samples"],
            "initial_c":_state["initial_c"],
            "ambient_c":_state["ambient_c"],
            "tau_s":_state["tau_s"],
        }

    def stop(args):
        _state["running"] = False
        return status({})

    registry.register("cooling_start", start)
    registry.register("cooling_sample", sample)
    registry.register("cooling_status", status)
    registry.register("cooling_stop", stop)
