"""Small power-loss-conscious persistence helpers for MicroPython.

The goal is not to pretend a microcontroller filesystem is transactional.  Instead we
keep at least one previously valid journal slot while writing the next one, and make
recovery decisions from both the journal and the actual staged-file length.
"""
try:
    import uos as os
except ImportError:
    import os
try:
    import ujson as json
except ImportError:
    import json
try:
    import ubinascii as binascii
except ImportError:
    import binascii

from sdl.util import ensure_dir, dirname, exists, remove_if_exists


def _sync_fs():
    fn = getattr(os, "sync", None)
    if fn:
        try:
            fn()
        except Exception:
            pass


def _flush_file(f):
    try:
        f.flush()
    except Exception:
        pass
    _sync_fs()


def file_size(path):
    try:
        return int(os.stat(path)[6])
    except OSError:
        return -1


def crc32_bytes(data):
    return binascii.crc32(data) & 0xffffffff


def crc32_tail(path, offset, length):
    crc = 0
    left = int(length)
    with open(path, "rb") as f:
        f.seek(int(offset))
        while left > 0:
            b = f.read(min(256, left))
            if not b:
                break
            crc = binascii.crc32(b, crc)
            left -= len(b)
    if left != 0:
        return None
    return crc & 0xffffffff


def _write_bytes_atomic(path, data):
    ensure_dir(dirname(path))
    tmp = path + ".tmp"
    remove_if_exists(tmp)
    with open(tmp, "wb") as f:
        f.write(data)
        _flush_file(f)
    # This helper is used for files whose older copy is preserved elsewhere.
    remove_if_exists(path)
    os.rename(tmp, path)
    _sync_fs()


def write_json_marker(path, obj):
    """Create/replace a small marker. Caller must preserve safety if power is lost.

    Install markers are created *before* any destructive promotion.  Therefore failure
    before this function finishes leaves the old application untouched.
    """
    raw = json.dumps(obj).encode("utf-8")
    _write_bytes_atomic(path, raw)
    return obj


class DualSlotJournal:
    """Alternating two-slot journal with an integrity check over exact JSON bytes."""
    def __init__(self, base_path):
        self.base_path = base_path
        self.paths = (base_path + ".a", base_path + ".b")
        self.generation = -1
        self.payload = None

    def _decode_slot(self, path):
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError:
            return None
        try:
            p1 = raw.find(b"\n")
            p2 = raw.find(b"\n", p1 + 1)
            if p1 <= 0 or p2 <= p1:
                return None
            generation = int(raw[:p1].decode())
            expected = int(raw[p1+1:p2].decode(), 16)
            body = raw[p2+1:]
            if crc32_bytes(body) != expected:
                return None
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, dict):
                return None
            return generation, payload
        except Exception:
            return None

    def read(self, default=None):
        best = None
        for path in self.paths:
            item = self._decode_slot(path)
            if item is not None and (best is None or item[0] > best[0]):
                best = item
        if best is None:
            self.generation = -1
            self.payload = default
            return default
        self.generation, self.payload = best
        return self.payload

    def write(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("journal payload must be dict")
        if self.generation < 0:
            self.read(None)
        generation = self.generation + 1
        body = json.dumps(payload).encode("utf-8")
        crc = crc32_bytes(body)
        raw = ("%d\n%08X\n" % (generation, crc)).encode("ascii") + body
        target = self.paths[generation & 1]
        _write_bytes_atomic(target, raw)
        # Read back the newly written slot before considering it current.
        check = self._decode_slot(target)
        if check is None or check[0] != generation:
            raise OSError("journal read-back verification failed")
        self.generation = generation
        self.payload = payload
        return payload

    def clear(self):
        for path in self.paths:
            remove_if_exists(path)
            remove_if_exists(path + ".tmp")
        # Remove the legacy single-file journal if present.
        remove_if_exists(self.base_path)
        remove_if_exists(self.base_path + ".tmp")
        self.generation = -1
        self.payload = None


def repair_prefix(path, committed_size):
    """Restore a file to exactly the committed prefix without in-place truncate.

    A side copy is completed first. The old file is then renamed aside, the repaired
    file is promoted, and finally the old copy is removed. Recovery can restore the
    .repair_old copy if power disappears in the narrow rename interval.
    """
    committed_size = int(committed_size)
    old = path + ".repair_old"
    tmp = path + ".repair_new"

    # Recover an interrupted previous repair first.
    if not exists(path) and exists(old):
        os.rename(old, path)
    remove_if_exists(tmp)

    with open(path, "rb") as src, open(tmp, "wb") as dst:
        left = committed_size
        while left > 0:
            b = src.read(min(256, left))
            if not b:
                raise OSError("staged file shorter than committed prefix")
            dst.write(b)
            left -= len(b)
        _flush_file(dst)

    remove_if_exists(old)
    os.rename(path, old)
    os.rename(tmp, path)
    _sync_fs()
    remove_if_exists(old)
    return committed_size
