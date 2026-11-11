class DeviceError(Exception):
    pass


class LogicalDevice:
    def __init__(self, device_id, direction, model, backend, read_fn=None, write_fn=None, meta=None):
        self.id = device_id
        self.direction = direction
        self.model = model
        self.backend = backend
        self.read_fn = read_fn
        self.write_fn = write_fn
        self.meta = meta or {}

    @property
    def readable(self):
        return self.read_fn is not None

    @property
    def writable(self):
        return self.write_fn is not None


class DeviceRegistry:
    def __init__(self):
        self._devices = {}

    def register(self, dev):
        if dev.id in self._devices:
            raise DeviceError("duplicate device id: %s" % dev.id)
        self._devices[dev.id] = dev

    def has(self, device_id):
        return device_id in self._devices

    def get(self, device_id):
        dev = self._devices.get(device_id)
        if dev is None:
            raise DeviceError("unknown device: %s" % device_id)
        return dev

    def list(self):
        return [self._devices[k] for k in sorted(self._devices)]

    def read(self, device_id):
        dev = self.get(device_id)
        if not dev.readable:
            raise DeviceError("device not readable: %s" % device_id)
        value = dev.read_fn()
        if isinstance(value, dict):
            result = dict(value)
        else:
            result = {"value": value}
        result.setdefault("id", dev.id)
        result.setdefault("model", dev.model)
        result.setdefault("backend", dev.backend)
        result.setdefault("status", "ok")
        return result

    def write(self, device_id, value):
        dev = self.get(device_id)
        if not dev.writable:
            raise DeviceError("device not writable: %s" % device_id)
        result = dev.write_fn(value)
        if isinstance(result, dict):
            out = dict(result)
        else:
            out = {"value": result}
        out.setdefault("id", dev.id)
        out.setdefault("model", dev.model)
        out.setdefault("backend", dev.backend)
        out.setdefault("status", "ok")
        return out
