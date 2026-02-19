from pathlib import Path
from datetime import datetime
from .utils import ensure_dir

def run_log_path(data_root: str, run_id: int) -> Path:
    return Path(data_root) / "logs" / f"run_{run_id}.log"

def append_log(data_root: str, run_id: int, message: str):
    p = run_log_path(data_root, run_id)
    ensure_dir(p.parent)
    ts = datetime.utcnow().isoformat()
    with p.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")

def tail_log(data_root: str, run_id: int, n: int = 200) -> str:
    p = run_log_path(data_root, run_id)
    if not p.exists():
        return ""
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    return "\n".join(lines[-n:])
