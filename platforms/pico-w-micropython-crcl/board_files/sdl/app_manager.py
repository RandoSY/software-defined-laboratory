try:
    import uos as os
except ImportError:
    import os

from sdl.util import exists, read_text, remove_if_exists, dirname, ensure_dir, ticks_ms
from sdl.durable import write_json_marker
try:
    import ujson as json
except ImportError:
    import json


class AppError(Exception):
    pass


class AppContext:
    """Trusted application context. This is an API boundary, not a security sandbox."""
    def __init__(self, lab, capabilities, emit=None):
        self.lab = lab
        self.devices = lab.devices
        self.capabilities = capabilities
        self.emit = emit or (lambda *args, **kwargs: None)

    def now_ms(self):
        return ticks_ms()


class AppManager:
    """Resident manager for the replaceable CRCL application.

    v1.1 adds a conservative install marker. The marker is written before any active
    application is moved. If reset/power loss occurs before COMMIT, startup restores
    the pre-install application rather than guessing that the candidate was healthy.
    """
    def __init__(self, config, lab, capabilities, emit=None):
        ccfg = config["crcl"]
        self.active_path = ccfg["active_path"]
        self.backup_path = ccfg["backup_path"]
        self.stage_path = ccfg["stage_path"]
        self.install_marker_path = ccfg.get("install_marker_path", self.stage_path + ".install.json")
        self.previous_backup_path = ccfg.get("previous_backup_path", self.backup_path + ".previous")
        self.recovery_failed_path = ccfg.get("recovery_failed_path", self.stage_path + ".recovery_failed")
        self.lab = lab
        self.capabilities = capabilities
        self.ctx = AppContext(lab, capabilities, emit)
        self.namespace = None
        self.running = False
        self.last_error = None
        self.failures = 0
        self.loaded_at_ms = None
        self.recovery_note = ""
        ensure_dir(dirname(self.active_path))
        ensure_dir(dirname(self.backup_path))
        ensure_dir(dirname(self.stage_path))
        self._recover_interrupted_install()

    def _load_marker(self):
        try:
            with open(self.install_marker_path, "r") as f:
                obj = json.loads(f.read())
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    def _preserve_as(self, src, dst):
        remove_if_exists(dst)
        if exists(src):
            try:
                os.rename(src, dst)
                return True
            except OSError:
                return False
        return False

    def _recover_interrupted_install(self):
        marker = self._load_marker()
        if marker is None:
            # Clean up an orphaned previous-backup file from a fully committed install
            # only when the normal backup slot is absent.
            if exists(self.previous_backup_path) and not exists(self.backup_path):
                try:
                    os.rename(self.previous_backup_path, self.backup_path)
                except OSError:
                    pass
            return

        had_active = bool(marker.get("had_active", False))
        had_prior_backup = bool(marker.get("had_prior_backup", False))
        active = exists(self.active_path)
        backup = exists(self.backup_path)
        stage = exists(self.stage_path)
        previous = exists(self.previous_backup_path)

        try:
            if had_active:
                if stage:
                    # Candidate has not been promoted yet. If active disappeared but a
                    # fresh backup exists, restore it. Otherwise the old active remains.
                    if not active and backup:
                        os.rename(self.backup_path, self.active_path)
                        active = True
                        backup = False
                    # Restore the older rollback slot if we temporarily moved it aside.
                    if had_prior_backup and previous and not backup:
                        os.rename(self.previous_backup_path, self.backup_path)
                        backup = True
                        previous = False
                    self.recovery_note = "interrupted install recovered before promotion"
                else:
                    # Stage vanished, so promotion may have happened. Conservatively
                    # reject the candidate and restore the known-good active backup.
                    if active:
                        self._preserve_as(self.active_path, self.recovery_failed_path)
                        active = False
                    if backup:
                        os.rename(self.backup_path, self.active_path)
                        active = True
                        backup = False
                        self.recovery_note = "interrupted promoted candidate rolled back"
                    elif previous:
                        # We lost the immediate backup but still have the older rollback
                        # generation. Prefer a known older app over an uncertain candidate.
                        os.rename(self.previous_backup_path, self.active_path)
                        active = True
                        previous = False
                        self.recovery_note = "recovered from previous backup generation"
                    else:
                        self.recovery_note = "install interrupted; no known-good backup available"

                    if had_prior_backup and previous and not exists(self.backup_path):
                        try:
                            os.rename(self.previous_backup_path, self.backup_path)
                        except OSError:
                            pass
            else:
                # First-ever app install. Until commit, an active candidate is uncertain.
                if not stage and active:
                    self._preserve_as(self.active_path, self.recovery_failed_path)
                    self.recovery_note = "uncommitted first install removed"
                else:
                    self.recovery_note = "interrupted first install recovered before promotion"

            remove_if_exists(self.install_marker_path)
            remove_if_exists(self.install_marker_path + ".tmp")
        except Exception as exc:
            self.recovery_note = "install recovery incomplete: %s" % exc

    def _compile_path(self, path):
        source = read_text(path)
        return compile(source, path, "exec"), source

    def _new_namespace(self, path):
        return {
            "__name__": "crcl_app",
            "__file__": path,
        }

    def load(self, start=True):
        self.stop()
        if not exists(self.active_path):
            self.namespace = None
            self.running = False
            self.last_error = None
            return False
        code, _ = self._compile_path(self.active_path)
        ns = self._new_namespace(self.active_path)
        exec(code, ns, ns)
        self.namespace = ns
        self.loaded_at_ms = ticks_ms()
        self.failures = 0
        self.last_error = None

        health = ns.get("health")
        if callable(health):
            result = health(self.ctx)
            if result is False:
                raise AppError("health() returned False")

        if start:
            self.start()
        return True

    def start(self):
        if self.namespace is None:
            if not self.load(start=False):
                raise AppError("no active application")
        setup = self.namespace.get("setup")
        if callable(setup):
            setup(self.ctx)
        self.running = True
        return True

    def stop(self):
        if self.namespace is not None and self.running:
            try:
                fn = self.namespace.get("stop")
                if callable(fn):
                    fn(self.ctx)
            except Exception as exc:
                self.last_error = "stop: %s" % exc
        self.running = False

    def tick(self):
        if not self.running or self.namespace is None:
            return
        fn = self.namespace.get("tick")
        if fn is None:
            fn = self.namespace.get("loop")
        if not callable(fn):
            return
        try:
            fn(self.ctx)
            self.failures = 0
        except Exception as exc:
            self.failures += 1
            self.last_error = "%s" % exc
            if self.failures >= 3:
                self.running = False

    def status(self):
        return {
            "present": exists(self.active_path),
            "backup": exists(self.backup_path),
            "loaded": self.namespace is not None,
            "running": self.running,
            "failures": self.failures,
            "last_error": self.last_error or "",
            "loaded_at_ms": self.loaded_at_ms if self.loaded_at_ms is not None else -1,
            "recovery": self.recovery_note or "none",
        }

    def validate_staged(self):
        if not exists(self.stage_path):
            raise AppError("no staged application")
        _, source = self._compile_path(self.stage_path)
        return len(source.encode("utf-8"))

    def install_staged(self):
        """Promote a verified staging file, health-check it, and rollback on failure.

        COMMIT is represented by removal of install_marker_path. Any reboot while that
        marker remains will restore the pre-install application on next AppManager init.
        """
        self.validate_staged()
        self.stop()

        had_active = exists(self.active_path)
        had_prior_backup = exists(self.backup_path)
        marker = {
            "version": 1,
            "had_active": had_active,
            "had_prior_backup": had_prior_backup,
            "active_path": self.active_path,
            "backup_path": self.backup_path,
            "stage_path": self.stage_path,
        }
        write_json_marker(self.install_marker_path, marker)
        if not exists(self.install_marker_path):
            raise AppError("could not persist install marker")

        # Preserve the previous rollback generation until the new candidate commits.
        remove_if_exists(self.previous_backup_path)
        if had_prior_backup:
            os.rename(self.backup_path, self.previous_backup_path)

        try:
            if had_active:
                os.rename(self.active_path, self.backup_path)
            os.rename(self.stage_path, self.active_path)
            self.namespace = None
            self.load(start=True)

            # Candidate is healthy. Commit by removing the transaction marker last.
            remove_if_exists(self.previous_backup_path)
            remove_if_exists(self.install_marker_path)
            remove_if_exists(self.install_marker_path + ".tmp")
            return self.status()
        except Exception as exc:
            self.last_error = "install: %s" % exc
            # Same recovery policy as boot recovery: reject candidate and restore old app.
            if exists(self.active_path):
                self._preserve_as(self.active_path, self.stage_path + ".failed")
            if had_active and exists(self.backup_path):
                os.rename(self.backup_path, self.active_path)
            if had_prior_backup and exists(self.previous_backup_path) and not exists(self.backup_path):
                os.rename(self.previous_backup_path, self.backup_path)
            remove_if_exists(self.install_marker_path)
            remove_if_exists(self.install_marker_path + ".tmp")
            try:
                self.namespace = None
                if exists(self.active_path):
                    self.load(start=True)
                else:
                    self.running = False
            except Exception as rex:
                self.last_error += "; rollback load failed: %s" % rex
            raise AppError(self.last_error)

    def rollback(self):
        if not exists(self.backup_path):
            raise AppError("no backup application")
        self.stop()
        failed = self.stage_path + ".rolled_back"
        remove_if_exists(failed)
        if exists(self.active_path):
            self._preserve_as(self.active_path, failed)
        os.rename(self.backup_path, self.active_path)
        self.namespace = None
        self.load(start=True)
        return self.status()
