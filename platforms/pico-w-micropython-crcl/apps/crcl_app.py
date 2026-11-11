# CRCL managed application example.
# Contract:
#   health(ctx) -> False rejects the app
#   setup(ctx)  -> called once on start
#   tick(ctx)   -> called frequently; MUST return quickly
#   stop(ctx)   -> called before reload/replacement

_last = 0
_state = 0

def health(ctx):
    # Require only the PicoBricks LED if available; otherwise remain valid as a no-op app.
    return True

def setup(ctx):
    global _last, _state
    _last = ctx.now_ms()
    _state = 0
    if ctx.devices.has("pb.led"):
        ctx.devices.write("pb.led", 0)

def tick(ctx):
    global _last, _state
    now = ctx.now_ms()
    if now - _last < 1000:
        return
    _last = now
    _state = 0 if _state else 1
    if ctx.devices.has("pb.led"):
        ctx.devices.write("pb.led", _state)

def stop(ctx):
    if ctx.devices.has("pb.led"):
        ctx.devices.write("pb.led", 0)
