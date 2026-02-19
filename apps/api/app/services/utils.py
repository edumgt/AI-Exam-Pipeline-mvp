from pathlib import Path

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
