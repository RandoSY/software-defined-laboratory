try:
    import machine
except ImportError:
    machine = None

from sdl.util import load_config, sleep_ms, ticks_ms, ticks_diff, parse_int, parse_float
from sdl.protocol import (
    parse_wire_line, human_to_wire, ProtocolError, rsp, dat, end,
    err_lines, ok_lines, parse_addr
)
from sdl.lab import Lab
from sdl.capabilities import CapabilityRegistry, CapabilityManager, CapabilityError
from sdl.app_manager import AppManager, AppError
from sdl.crcl import CRCLManager, CRCLError
from sdl.wifi import WiFiManager


def _fmt_value(v):
    if isinstance(v, float):
        return "%.6g" % v
    if isinstance(v, bytes):
        try:
            import ubinascii as binascii
        except ImportError:
            import binascii
        return binascii.hexlify(v).decode().upper()
    if isinstance(v, (list, tuple)):
        return ",".join(_fmt_value(x) for x in v)
    return v


def _dat_from_dict(req_id, record_type, obj):
    fields = {}
    for k, v in obj.items():
        fields[k] = _fmt_value(v)
    return dat(req_id, record_type, **fields)


class Runtime:
    VERSION = "1.1.0"

    def __init__(self, config=None):
        self.config = config or load_config()
        self.start_ms = ticks_ms()
        self.reset_requested = False
        self._console_id = 1
        self.wifi = WiFiManager(self.config)
        self.lab = Lab(self.config)
        self.capabilities = CapabilityRegistry()
        self.cap_manager = CapabilityManager("/capabilities", self.capabilities, self.lab)
        self.cap_manager.load_all()
        self.app = AppManager(self.config, self.lab, self.capabilities, emit=self.emit_event)
        try:
            self.app.load(start=True)
        except Exception as exc:
            print("WARN,APP_LOAD,%s" % exc)
        self.crcl = CRCLManager(self.config, self.app)
        self.transports = []
        self.tcp = None
        self.console = None
        self.ble = None

    def uptime_ms(self):
        return ticks_diff(ticks_ms(), self.start_ms)

    def emit_event(self, *parts, **kwargs):
        text = "EVT " + " ".join(str(p) for p in parts)
        self.broadcast([text])

    def start(self):
        print("")
        print("Pico W SDL/CRCL Reference Node v%s" % self.VERSION)
        print("Node: %s" % self.config["node_name"])
        print("Devices: %d" % len(self.lab.devices.list()))
        print("Capabilities: %d" % len(self.capabilities.names()))

        if self.config["console"].get("enabled", True):
            try:
                from sdl.transport_console import ConsoleTransport
                self.console = ConsoleTransport(self.config["console"].get("prompt", "SDL> "))
                self.console.start()
                self.transports.append(self.console)
            except Exception as exc:
                print("WARN,CONSOLE,%s" % exc)

        wifi_ok = False
        if self.config["tcp"].get("enabled", True):
            wifi_ok = self.wifi.connect()
            if wifi_ok:
                try:
                    from sdl.transport_tcp import TCPLineServer
                    self.tcp = TCPLineServer(
                        self.config["tcp"]["port"],
                        self.config["tcp"].get("max_clients", 3),
                    )
                    self.tcp.start()
                    self.transports.append(self.tcp)
                    print("SDL ASCII TCP: %s:%d" % (self.wifi.ip, self.config["tcp"]["port"]))
                except Exception as exc:
                    print("WARN,TCP,%s" % exc)
            else:
                print("INFO,WIFI,OFFLINE,%s" % (self.wifi.error or "not configured"))

        if self.config["ble"].get("enabled", False):
            try:
                from sdl.transport_ble_nus import BLENUSTransport
                self.ble = BLENUSTransport(self.config["ble"].get("name", "Pico-SDL"))
                self.transports.append(self.ble)
                print("BLE NUS: enabled")
            except Exception as exc:
                print("WARN,BLE,%s" % exc)

        print("READY")
        return wifi_ok

    def broadcast(self, lines):
        if self.console:
            try:
                self.console.send("console", lines)
            except Exception:
                pass
        if self.tcp:
            for cid in list(self.tcp.clients):
                try:
                    self.tcp.send("tcp:%d" % cid, lines)
                except Exception:
                    pass
        if self.ble:
            for conn in list(self.ble.connections):
                try:
                    self.ble.send("ble:%d" % conn, lines)
                except Exception:
                    pass

    def _authorized(self, source, req):
        if source == "console":
            return True
        token = self.config["tcp"].get("auth_token", "")
        if not token:
            return True
        if req.verb in ("PING", "INFO", "VERSION", "HELP"):
            return True
        return req.get("TOKEN", "") == token

    def _help_lines(self, rid):
        items = [
            "PING", "INFO", "VERSION",
            "DEV.LIST", "DEV.READ ID=<id>", "DEV.WRITE ID=<id> VALUE=<value>",
            "I2C.SCAN", "I2C.READ ADDR=68 REG=75 N=1", "I2C.WRITE ADDR=68 REG=6B VALUE=00",
            "CAP.LIST", "CAP.CALL NAME=<command> [KEY=value ...]", "PKG.LIST",
            "APP.STATUS", "APP.START", "APP.STOP", "APP.RELOAD",
            "CRCL.STATUS", "CRCL.BEGIN SIZE=<n> CRC32=<8hex> [SHA256=<64hex>]",
            "CRCL.DATA SEQ=<n> B64=<base64>", "CRCL.END", "CRCL.INSTALL",
            "CRCL.ABORT", "CRCL.ROLLBACK", "SYS.RELOAD",
        ]
        lines = [rsp(rid, True, COUNT=len(items))]
        for item in items:
            lines.append(dat(rid, "HELP", command=item))
        lines.append(end(rid))
        return lines

    def dispatch(self, source, req):
        rid = req.id
        if not self._authorized(source, req):
            return err_lines(rid, "AUTH", "token_required")

        try:
            v = req.verb

            if v == "PING":
                return ok_lines(rid, NODE=self.config["node_name"], UPTIME_MS=self.uptime_ms())

            if v in ("INFO", "VERSION"):
                lines = [rsp(rid, True, NODE=self.config["node_name"])]
                lines.append(dat(rid, "INFO",
                                 runtime="PicoW-SDL-CRCL",
                                 version=self.VERSION,
                                 protocol=self.config["protocol_version"],
                                 profile=self.config["profile"],
                                 micropython=(getattr(__import__("sys"), "implementation", None) is not None),
                                 ip=self.wifi.ip or "offline"))
                lines.append(end(rid))
                return lines

            if v == "HELP":
                return self._help_lines(rid)

            if v == "DEV.LIST":
                devs = self.lab.devices.list()
                lines = [rsp(rid, True, COUNT=len(devs))]
                for d in devs:
                    lines.append(dat(rid, "DEVICE",
                                     id=d.id, direction=d.direction,
                                     model=d.model, backend=d.backend,
                                     readable=int(d.readable), writable=int(d.writable)))
                lines.append(end(rid))
                return lines

            if v == "DEV.READ":
                did = req.get("ID")
                if not did:
                    return err_lines(rid, "ARG", "ID_required")
                result = self.lab.devices.read(did)
                return [rsp(rid, True, COUNT=1), _dat_from_dict(rid, "DEVICE", result), end(rid)]

            if v == "DEV.WRITE":
                did = req.get("ID")
                value = req.get("VALUE")
                if did is None or value is None:
                    return err_lines(rid, "ARG", "ID_and_VALUE_required")
                result = self.lab.devices.write(did, value)
                return [rsp(rid, True, COUNT=1), _dat_from_dict(rid, "DEVICE", result), end(rid)]

            if v == "I2C.SCAN":
                if not self.lab.i2c_bus:
                    return err_lines(rid, "NO_DEVICE", "i2c0_unavailable")
                addrs = self.lab.i2c_bus.scan()
                lines = [rsp(rid, True, COUNT=len(addrs))]
                for a in addrs:
                    lines.append(dat(rid, "I2C", address="0x%02X" % a))
                lines.append(end(rid))
                return lines

            if v == "I2C.READ":
                if not self.lab.i2c_bus:
                    return err_lines(rid, "NO_DEVICE", "i2c0_unavailable")
                addr = parse_addr(req.get("ADDR"))
                reg = parse_addr(req.get("REG"))
                n = parse_int(req.get("N", "1"), 1)
                if addr is None or reg is None:
                    return err_lines(rid, "ARG", "ADDR_and_REG_required")
                data_bytes = self.lab.i2c_bus.readn(addr, reg, n)
                return [rsp(rid, True, COUNT=len(data_bytes)),
                        dat(rid, "I2C", address="0x%02X" % addr,
                            register="0x%02X" % reg,
                            hex="".join("%02X" % b for b in data_bytes)),
                        end(rid)]

            if v == "I2C.WRITE":
                if not self.lab.i2c_bus:
                    return err_lines(rid, "NO_DEVICE", "i2c0_unavailable")
                addr = parse_addr(req.get("ADDR"))
                reg = parse_addr(req.get("REG"))
                val = parse_addr(req.get("VALUE"))
                if None in (addr, reg, val):
                    return err_lines(rid, "ARG", "ADDR_REG_VALUE_required")
                self.lab.i2c_bus.write8(addr, reg, val)
                return ok_lines(rid, ADDR="0x%02X" % addr, REG="0x%02X" % reg)

            if v == "CAP.LIST":
                names = self.capabilities.names()
                lines = [rsp(rid, True, COUNT=len(names))]
                for name in names:
                    lines.append(dat(rid, "CAPABILITY", name=name, owner=self.capabilities.owner(name)))
                lines.append(end(rid))
                return lines

            if v == "PKG.LIST":
                pkgs = self.cap_manager.list_packages()
                lines = [rsp(rid, True, COUNT=len(pkgs))]
                for p in pkgs:
                    lines.append(_dat_from_dict(rid, "PACKAGE", p))
                lines.append(end(rid))
                return lines

            if v == "CAP.CALL":
                name = req.get("NAME")
                if not name:
                    return err_lines(rid, "ARG", "NAME_required")
                args = dict(req.args)
                args.pop("NAME", None)
                args.pop("TOKEN", None)
                result = self.capabilities.call(name, args)
                lines = [rsp(rid, True, COUNT=1)]
                if isinstance(result, dict):
                    lines.append(_dat_from_dict(rid, "CAPABILITY", result))
                else:
                    lines.append(dat(rid, "CAPABILITY", name=name, value=_fmt_value(result)))
                lines.append(end(rid))
                return lines

            if v == "APP.STATUS":
                return [rsp(rid, True), _dat_from_dict(rid, "APP", self.app.status()), end(rid)]

            if v == "APP.START":
                self.app.start()
                return ok_lines(rid, RUNNING=1)

            if v == "APP.STOP":
                self.app.stop()
                return ok_lines(rid, RUNNING=0)

            if v == "APP.RELOAD":
                self.app.load(start=True)
                return ok_lines(rid, RUNNING=1)

            if v == "CRCL.STATUS":
                return [rsp(rid, True), _dat_from_dict(rid, "CRCL", self.crcl.status()), end(rid)]

            if v == "CRCL.BEGIN":
                size = parse_int(req.get("SIZE"), None)
                crc = req.get("CRC32")
                sha = req.get("SHA256")
                if size is None or crc is None:
                    return err_lines(rid, "ARG", "SIZE_and_CRC32_required")
                st = self.crcl.begin(size, crc, sha)
                return [rsp(rid, True), _dat_from_dict(rid, "CRCL", st), end(rid)]

            if v == "CRCL.DATA":
                seq = parse_int(req.get("SEQ"), None)
                b64 = req.get("B64")
                if seq is None or not b64:
                    return err_lines(rid, "ARG", "SEQ_and_B64_required")
                st = self.crcl.data(seq, b64)
                return [rsp(rid, True), _dat_from_dict(rid, "CRCL", st), end(rid)]

            if v == "CRCL.END":
                st = self.crcl.end()
                return [rsp(rid, True), _dat_from_dict(rid, "CRCL", st), end(rid)]

            if v == "CRCL.INSTALL":
                st = self.crcl.install()
                return [rsp(rid, True), _dat_from_dict(rid, "APP", st), end(rid)]

            if v == "CRCL.ABORT":
                st = self.crcl.abort()
                return [rsp(rid, True), _dat_from_dict(rid, "CRCL", st), end(rid)]

            if v == "CRCL.ROLLBACK":
                st = self.crcl.rollback()
                return [rsp(rid, True), _dat_from_dict(rid, "APP", st), end(rid)]

            if v == "SYS.RELOAD":
                self.reset_requested = True
                return ok_lines(rid, ACTION="soft_reset")

            return err_lines(rid, "UNKNOWN_VERB", v)

        except Exception as exc:
            return err_lines(rid, "EXCEPTION", str(exc))

    def handle_line(self, source, line):
        if not line.strip():
            return
        try:
            wire = line
            if not line.lstrip().upper().startswith("CMD "):
                wire = human_to_wire(line, str(self._console_id))
                self._console_id += 1
            req = parse_wire_line(wire)
            lines = self.dispatch(source, req)
        except ProtocolError as exc:
            lines = err_lines("0", "PARSE", str(exc))
        except Exception as exc:
            lines = err_lines("0", "EXCEPTION", str(exc))

        for t in self.transports:
            try:
                t.send(source, lines)
            except Exception:
                pass

    def loop_once(self):
        for t in self.transports:
            try:
                events = t.poll()
            except Exception:
                events = []
            for event, source, payload in events:
                if event == "line":
                    self.handle_line(source, payload)
                elif event == "connect":
                    try:
                        t.send(source, [
                            "EVT 0 CONNECT NODE=%s RUNTIME=%s" % (self.config["node_name"], self.VERSION)
                        ])
                    except Exception:
                        pass
        try:
            self.app.tick()
        except Exception:
            pass

        if self.reset_requested:
            sleep_ms(100)
            if machine is not None:
                machine.soft_reset()
            self.reset_requested = False

    def run_forever(self):
        self.start()
        while True:
            self.loop_once()
            sleep_ms(5)


def run():
    Runtime().run_forever()
