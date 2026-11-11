import sys

class ConsoleTransport:
    def __init__(self, prompt="SDL> "):
        self.prompt = prompt
        self.poller = None
        self.buf = ""
        try:
            try:
                import uselect as select
            except ImportError:
                import select
            self.poller = select.poll()
            self.poller.register(sys.stdin, select.POLLIN)
        except Exception:
            self.poller = None

    def start(self):
        try:
            sys.stdout.write(self.prompt)
        except Exception:
            pass

    def poll(self):
        out = []
        if self.poller is None:
            return out
        try:
            ready = self.poller.poll(0)
        except Exception:
            return out
        if not ready:
            return out
        try:
            ch = sys.stdin.read(1)
        except Exception:
            return out
        if not ch:
            return out
        if ch in ("\r", "\n"):
            line = self.buf
            self.buf = ""
            if line.strip():
                out.append(("line", "console", line))
            return out
        if ch in ("\x08", "\x7f"):
            self.buf = self.buf[:-1]
            return out
        if ch == "\x15":  # Ctrl-U
            self.buf = ""
            return out
        if 32 <= ord(ch) <= 126 and len(self.buf) < 2048:
            self.buf += ch
        return out

    def send(self, source, lines):
        if source != "console":
            return
        try:
            sys.stdout.write("\r\n".join(lines) + "\r\n" + self.prompt)
        except Exception:
            pass
