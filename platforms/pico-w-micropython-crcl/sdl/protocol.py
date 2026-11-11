from sdl.util import safe_token, parse_int, parse_float


class ProtocolError(Exception):
    pass


class Request:
    def __init__(self, req_id, verb, args=None, raw=""):
        self.id = str(req_id)
        self.verb = str(verb).upper()
        self.args = args or {}
        self.raw = raw

    def get(self, key, default=None):
        return self.args.get(str(key).upper(), default)


def _split_tokens(line):
    # Deliberately simple wire grammar: space-separated tokens, KEY=VALUE pairs.
    # Values should not contain spaces; encode structured/binary content as Base64.
    return [x for x in line.strip().split() if x]


def parse_wire_line(line):
    parts = _split_tokens(line)
    if len(parts) < 3 or parts[0].upper() != "CMD":
        raise ProtocolError("expected: CMD <id> <verb> [KEY=value ...]")
    req_id = parts[1]
    verb = parts[2].upper()
    args = {}
    positional = []
    for tok in parts[3:]:
        if "=" in tok:
            k, v = tok.split("=", 1)
            args[k.upper()] = v
        else:
            positional.append(tok)
    if positional:
        args["_POS"] = positional
    return Request(req_id, verb, args, raw=line)


def human_to_wire(line, req_id="0"):
    s = line.strip()
    if not s:
        return None
    if s.upper().startswith("CMD "):
        return s

    p = s.split()
    u = [x.upper() for x in p]
    if u[0] in ("?", "HELP"):
        return "CMD %s HELP" % req_id
    if u[0] == "PING":
        return "CMD %s PING" % req_id
    if u[0] in ("INFO", "ID", "IDENTIFY"):
        return "CMD %s INFO" % req_id
    if u[0] in ("VERSION", "VER"):
        return "CMD %s VERSION" % req_id

    if len(u) >= 2 and u[0] == "DEV":
        if u[1] == "LIST":
            return "CMD %s DEV.LIST" % req_id
        if u[1] == "READ" and len(p) >= 3:
            return "CMD %s DEV.READ ID=%s" % (req_id, p[2])
        if u[1] == "WRITE" and len(p) >= 4:
            return "CMD %s DEV.WRITE ID=%s VALUE=%s" % (req_id, p[2], p[3])

    if len(u) >= 2 and u[0] == "I2C":
        if u[1] == "SCAN":
            return "CMD %s I2C.SCAN" % req_id
        if u[1] == "READ" and len(p) >= 4:
            n = p[4] if len(p) >= 5 else "1"
            return "CMD %s I2C.READ ADDR=%s REG=%s N=%s" % (req_id, p[2], p[3], n)
        if u[1] == "WRITE" and len(p) >= 5:
            return "CMD %s I2C.WRITE ADDR=%s REG=%s VALUE=%s" % (req_id, p[2], p[3], p[4])

    if len(u) >= 2 and u[0] == "CAP":
        if u[1] == "LIST":
            return "CMD %s CAP.LIST" % req_id
        if u[1] == "CALL" and len(p) >= 3:
            extras = " ".join(p[3:])
            return ("CMD %s CAP.CALL NAME=%s %s" % (req_id, p[2], extras)).strip()

    if len(u) >= 2 and u[0] == "APP":
        if u[1] == "STATUS":
            return "CMD %s APP.STATUS" % req_id
        if u[1] == "START":
            return "CMD %s APP.START" % req_id
        if u[1] == "STOP":
            return "CMD %s APP.STOP" % req_id
        if u[1] == "RELOAD":
            return "CMD %s APP.RELOAD" % req_id

    if len(u) >= 2 and u[0] == "CRCL":
        # Human console access to administrative verbs.
        verb = "CRCL." + u[1]
        extras = " ".join(p[2:])
        return ("CMD %s %s %s" % (req_id, verb, extras)).strip()

    if len(u) >= 2 and u[0] == "SYS" and u[1] == "RELOAD":
        return "CMD %s SYS.RELOAD" % req_id

    # Convenience direct logical-device names.
    if u[0] in ("TEMP", "TEMPERATURE"):
        return "CMD %s DEV.READ ID=temp1" % req_id
    if u[0] in ("DIST", "DISTANCE"):
        return "CMD %s DEV.READ ID=distance1" % req_id
    if u[0] in ("MASS", "WEIGHT"):
        return "CMD %s DEV.READ ID=mass1" % req_id

    raise ProtocolError("unknown human command")


def rsp(req_id, ok=True, **fields):
    parts = ["RSP", str(req_id), "OK" if ok else "ERR"]
    for k, v in fields.items():
        if v is None:
            continue
        parts.append("%s=%s" % (k.upper(), safe_token(v)))
    return " ".join(parts)


def dat(req_id, record_type, **fields):
    parts = ["DAT", str(req_id), str(record_type).upper()]
    for k, v in fields.items():
        if v is None:
            continue
        parts.append("%s=%s" % (k, safe_token(v)))
    return " ".join(parts)


def end(req_id):
    return "END %s" % req_id


def err_lines(req_id, code, message):
    return [rsp(req_id, False, CODE=code, MSG=message), end(req_id)]


def ok_lines(req_id, **fields):
    return [rsp(req_id, True, **fields), end(req_id)]


def parse_addr(s):
    if s is None:
        return None
    s = str(s).strip()
    try:
        if s.lower().startswith("0x"):
            return int(s, 16)
        # I2C console convention: bare 68 means hex 0x68, not decimal 68.
        return int(s, 16)
    except Exception:
        return None
