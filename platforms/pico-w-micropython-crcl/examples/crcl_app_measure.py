"""Example dynamically delivered CRCL app: periodically report a measurement.

It chooses temp1 when a physical DS18B20 is installed, then cpu_temp, then pb.pot.
The app never blocks the resident supervisor for long.
"""
_last = 0
_source = None

def health(ctx):
    return ctx.devices.has("temp1") or ctx.devices.has("cpu_temp") or ctx.devices.has("pb.pot")

def setup(ctx):
    global _last, _source
    for candidate in ("temp1", "cpu_temp", "pb.pot"):
        if ctx.devices.has(candidate):
            _source = candidate
            break
    _last = ctx.now_ms()
    ctx.emit("APP", "START", _source)

def tick(ctx):
    global _last
    now = ctx.now_ms()
    if now - _last < 2000:
        return
    _last = now
    data = ctx.devices.read(_source)
    ctx.emit("MEAS", _source, data)

def stop(ctx):
    ctx.emit("APP", "STOP", _source)
