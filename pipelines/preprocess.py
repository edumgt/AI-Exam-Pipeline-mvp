from __future__ import annotations
from pathlib import Path
import pandas as pd

def preprocess(source_path: str, out_dir: str, run_id: int) -> str:
    """
    MVP 전처리:
    - CSV 읽기
    - 결측치 처리(간단히 forward fill)
    - time 정렬
    - processed.csv 저장
    """
    src = Path(source_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(src)
    if "time" in df.columns:
        df = df.sort_values("time")
    df = df.ffill().bfill()

    processed_path = out / "processed.csv"
    df.to_csv(processed_path, index=False)
    return str(processed_path)
