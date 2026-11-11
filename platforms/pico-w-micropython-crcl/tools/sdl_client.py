#!/usr/bin/env python3
import argparse
import socket


class SDLClient:
    def __init__(self, host, port=8765, token="", timeout=5.0):
        self.host = host
        self.port = int(port)
        self.token = token
        self.timeout = float(timeout)
        self.sock = None
        self.file = None
        self.req_id = 100

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.sock.settimeout(self.timeout)
        self.file = self.sock.makefile("rwb", buffering=0)
        # Optional EVT CONNECT can arrive before first response.
        return self

    def close(self):
        try:
            if self.file:
                self.file.close()
        finally:
            if self.sock:
                self.sock.close()
        self.file = None
        self.sock = None

    def command(self, verb, **kwargs):
        rid = self.req_id
        self.req_id += 1
        fields = []
        for k, v in kwargs.items():
            if v is None:
                continue
            fields.append("%s=%s" % (k.upper(), v))
        if self.token and "TOKEN" not in {k.upper() for k in kwargs}:
            fields.append("TOKEN=%s" % self.token)
        line = "CMD %d %s%s\r\n" % (rid, verb.upper(), (" " + " ".join(fields)) if fields else "")
        self.file.write(line.encode("utf-8"))
        out = []
        while True:
            raw = self.file.readline()
            if not raw:
                raise ConnectionError("connection closed")
            text = raw.decode("utf-8", "replace").rstrip("\r\n")
            if text.startswith("EVT "):
                out.append(text)
                continue
            out.append(text)
            if text == "END %d" % rid:
                return out

    def __enter__(self):
        return self.connect()

    def __exit__(self, *args):
        self.close()


def main():
    ap = argparse.ArgumentParser(description="SDL ASCII TCP client")
    ap.add_argument("host")
    ap.add_argument("verb")
    ap.add_argument("fields", nargs="*")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default="")
    ns = ap.parse_args()

    kwargs = {}
    for item in ns.fields:
        if "=" not in item:
            ap.error("field must be KEY=VALUE: %s" % item)
        k, v = item.split("=", 1)
        kwargs[k] = v

    with SDLClient(ns.host, ns.port, ns.token) as c:
        for line in c.command(ns.verb, **kwargs):
            print(line)


if __name__ == "__main__":
    main()
