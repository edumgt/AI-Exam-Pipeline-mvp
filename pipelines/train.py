from __future__ import annotations
from pathlib import Path
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

def train(processed_path: str, out_dir: str, run_id: int, model_type: str = "baseline_sklearn") -> str:
    """
    MVP 학습:
    - processed.csv에서 label 컬럼을 타깃으로 사용
    - 간단한 RandomForest로 학습
    - model.joblib 저장
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(processed_path)
    if "label" not in df.columns:
        raise ValueError("processed data must contain 'label' column for MVP training")

    X = df.drop(columns=["label"])
    y = df["label"]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    model_path = out / "model.joblib"
    joblib.dump({"model": model, "columns": list(X.columns)}, model_path)
    return str(model_path)
