try:
    import usocket as socket
except ImportError:
    import socket


class TCPLineServer:
    def __init__(self, port=8765, max_clients=3, max_line=2048):
        self.port = int(port)
        self.max_clients = int(max_clients)
        self.max_line = int(max_line)
        self.server = None
        self.clients = {}   # cid -> {"sock": sock, "buf": bytearray}
        self._next_id = 1

    def start(self, host="0.0.0.0"):
        s = socket.socket()
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass
        s.bind((host, self.port))
        s.listen(self.max_clients)
        s.setblocking(False)
        self.server = s

    def close(self):
        for cid in list(self.clients):
            self._drop(cid)
        if self.server:
            try:
                self.server.close()
            except Exception:
                pass
        self.server = None

    def _drop(self, cid):
        c = self.clients.pop(cid, None)
        if c:
            try:
                c["sock"].close()
            except Exception:
                pass

    def poll(self):
        events = []
        if self.server is None:
            return events

        # Accept all immediately available clients, capped.
        while len(self.clients) < self.max_clients:
            try:
                sock, addr = self.server.accept()
                sock.setblocking(False)
                cid = self._next_id
                self._next_id += 1
                self.clients[cid] = {"sock": sock, "buf": bytearray(), "addr": addr}
                events.append(("connect", "tcp:%d" % cid, str(addr)))
            except OSError:
                break

        for cid in list(self.clients):
            c = self.clients.get(cid)
            if c is None:
                continue
            try:
                data = c["sock"].recv(512)
                if data == b"":
                    self._drop(cid)
                    events.append(("disconnect", "tcp:%d" % cid, "closed"))
                    continue
                if data:
                    c["buf"].extend(data)
                    if len(c["buf"]) > self.max_line * 2:
                        self._drop(cid)
                        events.append(("disconnect", "tcp:%d" % cid, "line_buffer_overflow"))
                        continue
                    while True:
                        pos = c["buf"].find(b"\n")
                        if pos < 0:
                            break
                        raw = bytes(c["buf"][:pos])
                        del c["buf"][:pos+1]
                        if raw.endswith(b"\r"):
                            raw = raw[:-1]
                        if len(raw) > self.max_line:
                            events.append(("line", "tcp:%d" % cid, ""))
                            continue
                        try:
                            line = raw.decode("utf-8")
                        except Exception:
                            line = ""
                        events.append(("line", "tcp:%d" % cid, line))
            except OSError:
                # Normal non-blocking no-data condition.
                pass
            except Exception:
                self._drop(cid)
                events.append(("disconnect", "tcp:%d" % cid, "error"))
        return events

    def send(self, source, lines):
        if not source.startswith("tcp:"):
            return
        try:
            cid = int(source.split(":", 1)[1])
        except Exception:
            return
        c = self.clients.get(cid)
        if c is None:
            return
        payload = ("\r\n".join(lines) + "\r\n").encode("utf-8")
        try:
            view = memoryview(payload)
            sent = 0
            while sent < len(payload):
                n = c["sock"].send(view[sent:])
                if not n:
                    raise OSError("socket send returned zero")
                sent += n
        except Exception:
            self._drop(cid)
