from __future__ import annotations
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

def evaluate(processed_path: str, model_path: str, out_dir: str, run_id: int) -> dict:
    """
    MVP 평가:
    - train/val split을 동일 방식으로 다시 나누어 val 지표 산출(간단 예시)
    """
    bundle = joblib.load(model_path)
    model = bundle["model"]
    cols = bundle["columns"]

    df = pd.read_csv(processed_path)
    X = df[cols]
    y = df["label"]

    _, X_val, _, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    pred = model.predict(X_val)
    return {
        "accuracy": float(accuracy_score(y_val, pred)),
        "f1": float(f1_score(y_val, pred, average="weighted")),
        "precision": float(precision_score(y_val, pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_val, pred, average="weighted", zero_division=0)),
        "val_samples": int(len(y_val)),
    }
