try:
    import ujson as json
except ImportError:
    import json

try:
    import uos as os
except ImportError:
    import os

try:
    import utime as time
except ImportError:
    import time


def ticks_ms():
    fn = getattr(time, "ticks_ms", None)
    if fn:
        return fn()
    return int(time.time() * 1000)


def ticks_diff(a, b):
    fn = getattr(time, "ticks_diff", None)
    if fn:
        return fn(a, b)
    return a - b


def sleep_ms(ms):
    fn = getattr(time, "sleep_ms", None)
    if fn:
        fn(int(ms))
    else:
        time.sleep(ms / 1000.0)


def ensure_dir(path):
    if not path or path == "/":
        return
    parts = path.strip("/").split("/")
    cur = ""
    for part in parts:
        cur += "/" + part
        try:
            os.mkdir(cur)
        except OSError:
            pass


def dirname(path):
    if "/" not in path:
        return ""
    d = path.rsplit("/", 1)[0]
    return d or "/"


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def remove_if_exists(path):
    try:
        os.remove(path)
    except OSError:
        pass


def read_text(path):
    with open(path, "r") as f:
        return f.read()


def write_text(path, data):
    ensure_dir(dirname(path))
    with open(path, "w") as f:
        f.write(data)


def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.loads(f.read())
    except Exception:
        return default


def save_json(path, obj):
    ensure_dir(dirname(path))
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(json.dumps(obj))
    remove_if_exists(path)
    os.rename(tmp, path)


def merge_dict(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge_dict(dst[k], v)
        else:
            dst[k] = v
    return dst


def load_config():
    from config_default import CONFIG
    # shallow-deep copy without copy module assumptions
    cfg = json.loads(json.dumps(CONFIG))
    user = load_json("/config.json", None)
    if user:
        merge_dict(cfg, user)
    return cfg


def safe_token(s):
    # SDL token-safe output. Replace whitespace/control characters.
    out = []
    for ch in str(s):
        o = ord(ch)
        if ch in " \t\r\n=" or o < 32 or o > 126:
            out.append("_")
        else:
            out.append(ch)
    return "".join(out)


def parse_int(value, default=None):
    try:
        s = str(value).strip()
        if s.lower().startswith("0x"):
            return int(s, 16)
        return int(s)
    except Exception:
        return default


def parse_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def bool_value(value, default=False):
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "on", "enable", "enabled"):
        return True
    if s in ("0", "false", "no", "off", "disable", "disabled"):
        return False
    return default
