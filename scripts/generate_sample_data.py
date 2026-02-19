from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import os

DATA_ROOT = os.environ.get("DATA_ROOT", "/data")

def main():
    inbound = Path(DATA_ROOT) / "inbound"
    inbound.mkdir(parents=True, exist_ok=True)
    out = inbound / "sample_timeseries.csv"

    n = 500
    time = np.arange(n)
    s1 = np.sin(time / 10) + np.random.normal(0, 0.1, n)
    s2 = np.cos(time / 15) + np.random.normal(0, 0.1, n)
    # 간단한 규칙 기반 라벨
    label = (s1 + 0.5 * s2 > 0.3).astype(int)

    df = pd.DataFrame({
        "time": time,
        "sensor_1": s1,
        "sensor_2": s2,
        "label": label
    })
    df.to_csv(out, index=False)
    print(f"[OK] sample data written: {out}")

if __name__ == "__main__":
    main()
