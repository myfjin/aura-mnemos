"""Tests for mnemos health sidecar."""

import os
import sys
import json
import tempfile
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aura_mnemos import store


def _wait_for_server(url: str, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


def _set_temp_db(tmpdir: str) -> str:
    db_path = os.path.join(tmpdir, "mnemos.db")
    os.environ["MNEMOS_DB"] = db_path
    return db_path


def test_health_ok():
    tmpdir = tempfile.mkdtemp()
    proc = None
    try:
        db_path = _set_temp_db(tmpdir)
        store.init_db()

        env = os.environ.copy()
        env["PORT"] = "18080"
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
        proc = subprocess.Popen(
            [sys.executable, "-m", "aura_mnemos.health"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if not _wait_for_server("http://127.0.0.1:18080/health"):
            stdout, stderr = proc.communicate(timeout=2)
            raise AssertionError(
                f"server did not start: stdout={stdout.decode()} stderr={stderr.decode()}"
            )
        with urllib.request.urlopen("http://127.0.0.1:18080/health") as resp:
            body = json.loads(resp.read().decode())
        assert body["status"] == "ok", f"expected ok, got {body}"
        assert body["version"] == "0.1.0"
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_health_down_when_db_missing():
    tmpdir = tempfile.mkdtemp()
    proc = None
    try:
        os.environ["MNEMOS_DB"] = os.path.join(tmpdir, "does_not_exist", "mnemos.db")
        env = os.environ.copy()
        env["PORT"] = "18081"
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent)
        proc = subprocess.Popen(
            [sys.executable, "-m", "aura_mnemos.health"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if not _wait_for_server("http://127.0.0.1:18081/health"):
            stdout, stderr = proc.communicate(timeout=2)
            raise AssertionError(
                f"server did not start: stdout={stdout.decode()} stderr={stderr.decode()}"
            )
        with urllib.request.urlopen("http://127.0.0.1:18081/health") as resp:
            body = json.loads(resp.read().decode())
        status = body["status"]
        assert status != "ok", f"DISASTER DID NOT HAPPEN: status was {status}"
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    test_health_ok()
    print("PASS: health_ok")
    test_health_down_when_db_missing()
    print("PASS: health_down_when_db_missing")
    print("ALL PASSED")
