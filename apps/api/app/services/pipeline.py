from pathlib import Path
from .utils import ensure_dir

def make_run_dirs(data_root: str, run_id: int) -> dict:
    base = Path(data_root) / "runs" / f"run_{run_id}"
    processed = base / "processed"
    model_dir = base / "model"
    metrics_dir = base / "metrics"
    for p in [processed, model_dir, metrics_dir]:
        ensure_dir(p)
    return {
        "run_base": str(base),
        "processed_dir": str(processed),
        "model_dir": str(model_dir),
        "metrics_dir": str(metrics_dir),
    }
