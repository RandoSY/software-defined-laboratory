try:
    import ujson as json
except ImportError:
    import json
try:
    import uos as os
except ImportError:
    import os

from sdl.util import exists, read_text


class CapabilityError(Exception):
    pass


class CapabilityRegistry:
    """Transactional command registry for late-bound experiment capabilities."""
    def __init__(self):
        self._handlers = {}
        self._owners = {}

    def names(self):
        return sorted(self._handlers)

    def owner(self, name):
        return self._owners.get(name)

    def register(self, name, handler, owner="runtime"):
        key = str(name).strip().lower()
        if not key or not callable(handler):
            raise CapabilityError("invalid capability registration")
        if key in self._handlers:
            raise CapabilityError("duplicate capability command: %s" % key)
        self._handlers[key] = handler
        self._owners[key] = owner

    def call(self, name, args):
        key = str(name).strip().lower()
        fn = self._handlers.get(key)
        if fn is None:
            raise CapabilityError("unknown capability: %s" % name)
        return fn(args or {})

    def snapshot(self):
        return dict(self._handlers), dict(self._owners)

    def restore(self, snapshot):
        self._handlers, self._owners = snapshot

    def merge_from(self, other):
        for name in other.names():
            self.register(name, other._handlers[name], other._owners[name])


class CapabilityManager:
    def __init__(self, root="/capabilities", registry=None, lab=None):
        self.root = root
        self.registry = registry or CapabilityRegistry()
        self.lab = lab
        self.packages = {}

    def _listdirs(self):
        try:
            return os.listdir(self.root)
        except OSError:
            return []

    def _read_manifest(self, path):
        with open(path, "r") as f:
            return json.loads(f.read())

    def load_all(self):
        self.packages = {}
        for name in sorted(self._listdirs()):
            base = self.root.rstrip("/") + "/" + name
            try:
                st = os.stat(base)
            except OSError:
                continue
            # MicroPython and CPython mode bits differ; simply attempt expected files.
            if not exists(base + "/READY"):
                continue
            self._load_one(name, base)
        return self.packages

    def _load_one(self, name, base):
        manifest_path = base + "/manifest.json"
        module_path = base + "/module.py"
        try:
            manifest = self._read_manifest(manifest_path)
            if manifest.get("apiVersion") != "1.0.0":
                raise CapabilityError("unsupported apiVersion")
            package_id = manifest.get("id", name)
            promised = manifest.get("provides", [])
            required = (manifest.get("requires") or {}).get("sensors", [])
            missing = [d for d in required if not self.lab.devices.has(d)]
            if missing:
                self.packages[package_id] = {
                    "status": "disabled",
                    "reason": "missing_devices",
                    "missing": missing,
                    "version": manifest.get("version", "?"),
                }
                return

            source = read_text(module_path)
            code = compile(source, module_path, "exec")
            ns = {"__name__": "cap_%s" % package_id, "__file__": module_path}
            exec(code, ns, ns)
            register = ns.get("register")
            if not callable(register):
                raise CapabilityError("module.py lacks register(registry, lab)")

            shadow = CapabilityRegistry()
            # owner tagging is injected through a small façade.
            class OwnerRegistry:
                def register(self_inner, command, handler):
                    shadow.register(command, handler, package_id)
            register(OwnerRegistry(), self.lab)

            actual = shadow.names()
            if sorted(promised) != sorted(actual):
                raise CapabilityError("manifest provides != registered commands")
            # Transaction: only merge after the entire package validates.
            self.registry.merge_from(shadow)
            self.packages[package_id] = {
                "status": "active",
                "version": manifest.get("version", "?"),
                "provides": actual,
            }
        except Exception as exc:
            self.packages[name] = {
                "status": "error",
                "reason": str(exc),
            }

    def list_packages(self):
        out = []
        for k in sorted(self.packages):
            item = dict(self.packages[k])
            item["id"] = k
            out.append(item)
        return out
