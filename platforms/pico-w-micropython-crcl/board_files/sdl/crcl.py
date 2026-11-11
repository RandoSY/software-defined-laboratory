try:
    import uos as os
except ImportError:
    import os
try:
    import ubinascii as binascii
except ImportError:
    import binascii
try:
    import uhashlib as hashlib
except ImportError:
    try:
        import hashlib
    except ImportError:
        hashlib = None

from sdl.util import ensure_dir, dirname, remove_if_exists, exists, load_json
from sdl.durable import DualSlotJournal, file_size, crc32_tail, repair_prefix


class CRCLError(Exception):
    pass


def _hex32(value):
    return "%08X" % (int(value) & 0xffffffff)


def _sha256_file(path):
    if hashlib is None or not hasattr(hashlib, "sha256"):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(512)
            if not b:
                break
            h.update(b)
    d = h.digest()
    return binascii.hexlify(d).decode().upper()


def _crc32_file(path):
    crc = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(512)
            if not b:
                break
            crc = binascii.crc32(b, crc)
    return crc & 0xffffffff


class CRCLManager:
    """Managed single-file CRCL updater for /apps/crcl_app.py.

    v1.1 strengthens interruption recovery with two mechanisms:
      * a dual-slot, CRC-protected transfer journal; and
      * a pending-chunk record written before each append.

    On reboot a pending chunk is reconciled against the actual staged-file length.
    A complete appended chunk is committed if its tail CRC matches; a partial append
    is rolled back to the last committed prefix. This makes explicit --resume much
    safer after resets or power loss during DATA reception.
    """
    def __init__(self, config, app_manager):
        cfg = config["crcl"]
        self.stage_path = cfg["stage_path"]
        self.journal_path = cfg["journal_path"]
        self.max_bytes = int(cfg["max_bytes"])
        self.chunk_max_decoded = int(cfg["chunk_max_decoded"])
        self.app = app_manager
        self.state = None
        ensure_dir(dirname(self.stage_path))
        self.journal = DualSlotJournal(self.journal_path)
        self._recover_journal()

    def _recover_journal(self):
        # Restore an interrupted repair rename if necessary.
        repair_old = self.stage_path + ".repair_old"
        if not exists(self.stage_path) and exists(repair_old):
            try:
                os.rename(repair_old, self.stage_path)
            except OSError:
                pass

        j = self.journal.read(None)

        # One-time migration from the v1.0 single-file JSON journal.
        if j is None:
            legacy = load_json(self.journal_path, None)
            if isinstance(legacy, dict):
                j = legacy
                try:
                    self.journal.write(j)
                    remove_if_exists(self.journal_path)
                except Exception:
                    pass

        if not isinstance(j, dict) or not exists(self.stage_path):
            self.state = None
            return

        self.state = j
        self._reconcile_pending_chunk()

    def _save(self):
        if self.state is not None:
            self.journal.write(self.state)

    def _reconcile_pending_chunk(self):
        """Resolve the one DATA chunk that may have been in flight at reset."""
        pending = self.state.get("pending")
        if not pending:
            # Even without a pending record, never trust bytes beyond committed offset.
            committed = int(self.state.get("received", 0))
            actual = file_size(self.stage_path)
            if actual > committed:
                repair_prefix(self.stage_path, committed)
            elif actual >= 0 and actual < committed:
                self.state["state"] = "corrupt"
                self.state["error"] = "stage shorter than committed journal"
                self._save()
            return

        committed = int(self.state.get("received", 0))
        plen = int(pending.get("length", 0))
        pseq = int(pending.get("seq", -1))
        pcrc = str(pending.get("crc32", "")).upper()
        actual = file_size(self.stage_path)

        if actual == committed:
            # Journal landed, append did not: retry the same sequence explicitly.
            self.state["pending"] = None
            self._save()
            return

        if actual == committed + plen:
            tail = crc32_tail(self.stage_path, committed, plen)
            if tail is not None and _hex32(tail) == pcrc:
                # Entire chunk landed; make that fact durable now.
                self.state["received"] = actual
                self.state["next_seq"] = pseq + 1
                self.state["pending"] = None
                self._save()
                return

        if actual >= committed:
            # Partial/garbled append. Restore exactly the last committed prefix.
            repair_prefix(self.stage_path, committed)
            self.state["pending"] = None
            self.state["recovery"] = "partial_chunk_discarded"
            self._save()
            return

        self.state["state"] = "corrupt"
        self.state["error"] = "stage shorter than committed journal"
        self._save()

    def status(self):
        if self.state is None:
            return {"state": "idle", "stage_present": exists(self.stage_path)}
        out = dict(self.state)
        # Keep wire response compact and avoid nesting the pending dict in token output.
        pending = out.pop("pending", None)
        if pending:
            out["pending_seq"] = pending.get("seq", -1)
            out["pending_length"] = pending.get("length", 0)
        out["stage_present"] = exists(self.stage_path)
        out["stage_size"] = file_size(self.stage_path)
        return out

    def begin(self, size, crc32_hex, sha256_hex=None):
        size = int(size)
        if size < 1 or size > self.max_bytes:
            raise CRCLError("SIZE outside allowed range")
        crc32_hex = str(crc32_hex).replace("0x", "").upper().zfill(8)
        if len(crc32_hex) != 8:
            raise CRCLError("CRC32 must be 8 hex digits")
        try:
            int(crc32_hex, 16)
        except ValueError:
            raise CRCLError("invalid CRC32")

        if sha256_hex:
            sha256_hex = str(sha256_hex).upper()
            if len(sha256_hex) != 64:
                raise CRCLError("SHA256 must be 64 hex digits")
            try:
                int(sha256_hex, 16)
            except ValueError:
                raise CRCLError("invalid SHA256")

        remove_if_exists(self.stage_path)
        remove_if_exists(self.stage_path + ".repair_old")
        remove_if_exists(self.stage_path + ".repair_new")
        self.journal.clear()
        with open(self.stage_path, "wb") as f:
            try:
                f.flush()
            except Exception:
                pass
        self.state = {
            "state": "receiving",
            "size": size,
            "crc32": crc32_hex,
            "sha256": sha256_hex or "",
            "received": 0,
            "next_seq": 0,
            "pending": None,
        }
        self._save()
        return self.status()

    def data(self, seq, b64):
        if self.state is None or self.state.get("state") != "receiving":
            raise CRCLError("no receiving session")
        if self.state.get("pending"):
            # Normally only possible if a prior write failed without reboot.
            self._reconcile_pending_chunk()
            if self.state.get("pending"):
                raise CRCLError("pending DATA chunk requires recovery")
        seq = int(seq)
        if seq != int(self.state["next_seq"]):
            raise CRCLError("sequence mismatch expected=%d" % self.state["next_seq"])
        try:
            chunk = binascii.a2b_base64(b64)
        except Exception:
            raise CRCLError("invalid Base64")
        if not chunk:
            raise CRCLError("empty DATA chunk")
        if len(chunk) > self.chunk_max_decoded:
            raise CRCLError("chunk too large")
        new_total = int(self.state["received"]) + len(chunk)
        if new_total > int(self.state["size"]):
            raise CRCLError("received bytes exceed declared SIZE")

        # Durable intent first. If power goes away from here onward, reboot can
        # distinguish no append, full append, and partial append.
        self.state["pending"] = {
            "seq": seq,
            "length": len(chunk),
            "crc32": _hex32(binascii.crc32(chunk) & 0xffffffff),
        }
        self._save()

        with open(self.stage_path, "ab") as f:
            f.write(chunk)
            try:
                f.flush()
            except Exception:
                pass
        sync = getattr(os, "sync", None)
        if sync:
            try:
                sync()
            except Exception:
                pass

        actual = file_size(self.stage_path)
        if actual != new_total:
            # Leave pending state intact. Reconciliation will repair/recover.
            raise CRCLError("stage length after append is %d expected=%d" % (actual, new_total))

        self.state["received"] = new_total
        self.state["next_seq"] = seq + 1
        self.state["pending"] = None
        self._save()
        return {
            "seq": seq,
            "received": new_total,
            "remaining": int(self.state["size"]) - new_total,
        }

    def end(self):
        if self.state is None or self.state.get("state") != "receiving":
            raise CRCLError("no receiving session")
        if self.state.get("pending"):
            self._reconcile_pending_chunk()
        if self.state.get("state") != "receiving":
            raise CRCLError(self.state.get("error", "receiving state corrupt"))
        if int(self.state["received"]) != int(self.state["size"]):
            raise CRCLError("length mismatch")
        if file_size(self.stage_path) != int(self.state["size"]):
            raise CRCLError("staged file length disagrees with journal")
        actual_crc = _hex32(_crc32_file(self.stage_path))
        if actual_crc != self.state["crc32"]:
            raise CRCLError("CRC32 mismatch expected=%s actual=%s" % (self.state["crc32"], actual_crc))
        expected_sha = self.state.get("sha256") or ""
        actual_sha = _sha256_file(self.stage_path)
        if expected_sha:
            if actual_sha is None:
                raise CRCLError("SHA256 requested but unavailable")
            if actual_sha.upper() != expected_sha.upper():
                raise CRCLError("SHA256 mismatch")
        self.app.validate_staged()
        self.state["state"] = "verified"
        self.state["actual_crc32"] = actual_crc
        self.state["actual_sha256"] = actual_sha or ""
        self._save()
        return self.status()

    def install(self):
        if self.state is None or self.state.get("state") != "verified":
            raise CRCLError("staged application is not verified")
        try:
            result = self.app.install_staged()
            self.state["state"] = "installed"
            self._save()
            self.journal.clear()
            self.state = None
            return result
        except Exception as exc:
            if self.state is not None:
                self.state["state"] = "failed"
                self.state["error"] = str(exc)
                try:
                    self._save()
                except Exception:
                    pass
            raise CRCLError(str(exc))

    def abort(self):
        remove_if_exists(self.stage_path)
        remove_if_exists(self.stage_path + ".repair_old")
        remove_if_exists(self.stage_path + ".repair_new")
        self.journal.clear()
        self.state = None
        return {"state": "idle"}

    def rollback(self):
        result = self.app.rollback()
        self.abort()
        return result
