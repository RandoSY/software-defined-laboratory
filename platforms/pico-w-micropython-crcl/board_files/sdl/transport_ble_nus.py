# Optional Nordic UART Service (NUS) transport using MicroPython's low-level bluetooth API.
# Disabled by default. This keeps the core independent from aioble installation/version.

class BLENUSTransport:
    _IRQ_CENTRAL_CONNECT = 1
    _IRQ_CENTRAL_DISCONNECT = 2
    _IRQ_GATTS_WRITE = 3

    NUS_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    RX_UUID  = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
    TX_UUID  = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

    def __init__(self, name="Pico-SDL", max_line=1024):
        import bluetooth
        self.bluetooth = bluetooth
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.name = name
        self.max_line = max_line
        self.connections = set()
        self.queue = []
        self.buffers = {}
        self._setup()
        self.ble.irq(self._irq)
        self._advertise()

    def _setup(self):
        b = self.bluetooth
        UART_UUID = b.UUID(self.NUS_UUID)
        RX = (b.UUID(self.RX_UUID), b.FLAG_WRITE | b.FLAG_WRITE_NO_RESPONSE)
        TX = (b.UUID(self.TX_UUID), b.FLAG_NOTIFY)
        ((self.tx_handle, self.rx_handle),) = self.ble.gatts_register_services(((UART_UUID, (TX, RX)),))
        try:
            self.ble.gatts_set_buffer(self.rx_handle, 512, True)
        except Exception:
            pass

    def _adv_payload(self):
        # Flags + complete local name + complete 128-bit service UUID.
        import struct
        def field(t, value):
            return bytes((len(value) + 1, t)) + value
        payload = field(0x01, b"\x06")
        name = self.name.encode()
        payload += field(0x09, name[:26])
        # BLE UUID bytes are little-endian in advertising payload.
        hexstr = self.NUS_UUID.replace("-", "")
        try:
            import ubinascii as binascii
        except ImportError:
            import binascii
        raw = binascii.unhexlify(hexstr)[::-1]
        payload += field(0x07, raw)
        return payload

    def _advertise(self):
        try:
            self.ble.gap_advertise(100000, adv_data=self._adv_payload())
        except Exception as exc:
            print("WARN,BLE_ADV,%s" % exc)

    def _irq(self, event, data):
        if event == self._IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.connections.add(conn_handle)
            self.buffers[conn_handle] = bytearray()
            self.queue.append(("connect", "ble:%d" % conn_handle, "connected"))
        elif event == self._IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self.connections.discard(conn_handle)
            self.buffers.pop(conn_handle, None)
            self.queue.append(("disconnect", "ble:%d" % conn_handle, "closed"))
            self._advertise()
        elif event == self._IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle != self.rx_handle:
                return
            chunk = self.ble.gatts_read(self.rx_handle)
            buf = self.buffers.setdefault(conn_handle, bytearray())
            buf.extend(chunk)
            if len(buf) > self.max_line * 2:
                buf[:] = b""
                return
            while True:
                pos = buf.find(b"\n")
                if pos < 0:
                    break
                raw = bytes(buf[:pos])
                del buf[:pos+1]
                if raw.endswith(b"\r"):
                    raw = raw[:-1]
                try:
                    line = raw.decode("utf-8")
                except Exception:
                    line = ""
                self.queue.append(("line", "ble:%d" % conn_handle, line))

    def poll(self):
        q = self.queue
        self.queue = []
        return q

    def send(self, source, lines):
        if not source.startswith("ble:"):
            return
        try:
            conn = int(source.split(":",1)[1])
        except Exception:
            return
        if conn not in self.connections:
            return
        data = ("\r\n".join(lines) + "\r\n").encode()
        # Keep notifications conservative for default ATT MTU.
        for i in range(0, len(data), 20):
            try:
                self.ble.gatts_notify(conn, self.tx_handle, data[i:i+20])
            except Exception:
                break
