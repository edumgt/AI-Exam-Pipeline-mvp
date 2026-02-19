from __future__ import annotations

import os
import time
import hashlib
import threading
from pathlib import Path

import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


WATCH_DIR = Path(os.environ.get("WATCH_DIR", "/data/inbound"))
API_BASE = os.environ.get("API_BASE", "http://api:8000/api").rstrip("/")
STABLE_SECONDS = int(os.environ.get("STABLE_SECONDS", "10"))
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "1.0"))
AUTO_RUN = os.environ.get("AUTO_RUN", "true").lower() in ("1", "true", "yes", "y")

INCLUDE_EXT = set([e.strip().lower() for e in os.environ.get("INCLUDE_EXT", ".csv,.parquet,.json").split(",") if e.strip()])
IGNORE_SUFFIX = tuple([s.strip() for s in os.environ.get("IGNORE_SUFFIX", ".tmp,.partial").split(",") if s.strip()])
USE_DONE_FILE = os.environ.get("USE_DONE_FILE", "false").lower() in ("1", "true", "yes", "y")  # if true, process only when *.done exists

print(f"[watcher] WATCH_DIR={WATCH_DIR}")
print(f"[watcher] API_BASE={API_BASE}")
print(f"[watcher] STABLE_SECONDS={STABLE_SECONDS} POLL_INTERVAL={POLL_INTERVAL} AUTO_RUN={AUTO_RUN}")
print(f"[watcher] INCLUDE_EXT={sorted(INCLUDE_EXT)} IGNORE_SUFFIX={IGNORE_SUFFIX} USE_DONE_FILE={USE_DONE_FILE}")


def sha256_file(p: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def is_target_file(p: Path) -> bool:
    if not p.is_file():
        return False
    name = p.name.lower()
    if name.endswith(".done"):
        return False
    if name.endswith(IGNORE_SUFFIX):
        return False
    ext = p.suffix.lower()
    if INCLUDE_EXT and ext not in INCLUDE_EXT:
        return False
    return True


def wait_until_stable(p: Path, stable_seconds: int, poll: float) -> bool:
    """파일 크기가 stable_seconds 동안 변하지 않으면 True"""
    try:
        last_size = p.stat().st_size
    except FileNotFoundError:
        return False

    stable_for = 0.0
    while stable_for < stable_seconds:
        time.sleep(poll)
        try:
            size = p.stat().st_size
        except FileNotFoundError:
            return False
        if size == last_size:
            stable_for += poll
        else:
            last_size = size
            stable_for = 0.0
    return True


def done_file_ready(p: Path) -> bool:
    done = p.with_suffix(p.suffix + ".done")  # sample.csv.done
    return done.exists()


def create_dataset_and_run(p: Path):
    if USE_DONE_FILE and not done_file_ready(p):
        print(f"[watcher] waiting for done file: {p.name}")
        return

    print(f"[watcher] candidate: {p}")
    if not wait_until_stable(p, STABLE_SECONDS, POLL_INTERVAL):
        print(f"[watcher] not stable or missing: {p}")
        return

    try:
        st = p.stat()
        size = st.st_size
        mtime = int(st.st_mtime)
        checksum = sha256_file(p)
    except Exception as e:
        print(f"[watcher] metadata error: {p} -> {e}")
        return

    dataset_name = p.stem
    payload = {
        "name": dataset_name,
        "source_path": str(p),
        "meta": {
            "source": "nas_watcher",
            "file_name": p.name,
            "size_bytes": size,
            "mtime": mtime,
            "sha256": checksum
        }
    }

    try:
        r = requests.post(f"{API_BASE}/datasets", json=payload, timeout=30)
        if r.status_code >= 400:
            print(f"[watcher] create dataset failed: {r.status_code} {r.text}")
            return
        ds = r.json()
        print(f"[watcher] dataset created: id={ds.get('id')} path={ds.get('source_path')}")
    except Exception as e:
        print(f"[watcher] API error creating dataset: {e}")
        return

    if AUTO_RUN:
        try:
            r2 = requests.post(f"{API_BASE}/runs", json={"dataset_id": ds["id"], "model_type": "baseline_sklearn"}, timeout=30)
            if r2.status_code >= 400:
                print(f"[watcher] create run failed: {r2.status_code} {r2.text}")
                return
            run = r2.json()
            print(f"[watcher] run enqueued: id={run.get('id')} dataset_id={run.get('dataset_id')}")
        except Exception as e:
            print(f"[watcher] API error creating run: {e}")
            return


class Handler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._pending: dict[str, float] = {}
        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()

    def on_created(self, event):
        if event.is_directory:
            return
        self._mark(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        self._mark(event.dest_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._mark(event.src_path)

    def _mark(self, path_str: str):
        p = Path(path_str)
        if not is_target_file(p):
            return
        with self._lock:
            self._pending[str(p)] = time.time()

    def _loop(self):
        debounce = 2.0
        while True:
            time.sleep(1.0)
            now = time.time()
            to_process = []
            with self._lock:
                for k, t0 in list(self._pending.items()):
                    if now - t0 >= debounce:
                        to_process.append(k)
                        del self._pending[k]
            for k in to_process:
                threading.Thread(target=create_dataset_and_run, args=(Path(k),), daemon=True).start()


def main():
    WATCH_DIR.mkdir(parents=True, exist_ok=True)

    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR), recursive=False)
    observer.start()

    print("[watcher] started.")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("[watcher] stopping...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
