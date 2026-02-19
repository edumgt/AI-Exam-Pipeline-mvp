from __future__ import annotations
import json
import traceback
from pathlib import Path
from sqlalchemy.orm import Session

from app.workers.celery_app import celery
from app.config import settings
from app.db import SessionLocal, engine
from app.models import Base, RunStatus, StepStatus
from app import crud
from app.services.logs import append_log
from app.services.pipeline import make_run_dirs

# Ensure tables exist (MVP)
Base.metadata.create_all(bind=engine)

def _db() -> Session:
    return SessionLocal()

@celery.task(name="app.workers.tasks.run_pipeline")
def run_pipeline(run_id: int):
    db = _db()
    try:
        run = crud.get_run(db, run_id)
        if not run:
            return {"ok": False, "error": f"run {run_id} not found"}

        crud.set_run_status(db, run_id, RunStatus.running)
        append_log(settings.DATA_ROOT, run_id, f"Run started (dataset_id={run.dataset_id}, model_type={run.model_type})")

        dirs = make_run_dirs(settings.DATA_ROOT, run_id)

        # Step 1: preprocess
        crud.set_step_status(db, run_id, "preprocess", StepStatus.running)
        append_log(settings.DATA_ROOT, run_id, "Step preprocess: start")
        from pipelines.preprocess import preprocess
        processed_path = preprocess(
            source_path=run.dataset.source_path,
            out_dir=dirs["processed_dir"],
            run_id=run_id,
        )
        crud.set_step_status(db, run_id, "preprocess", StepStatus.success, message=f"processed={processed_path}")
        crud.update_run_artifacts_and_metrics(db, run_id, artifacts={"processed_path": processed_path})
        append_log(settings.DATA_ROOT, run_id, f"Step preprocess: done -> {processed_path}")

        # Step 2: train
        crud.set_step_status(db, run_id, "train", StepStatus.running)
        append_log(settings.DATA_ROOT, run_id, "Step train: start")
        from pipelines.train import train
        model_path = train(
            processed_path=processed_path,
            out_dir=dirs["model_dir"],
            run_id=run_id,
            model_type=run.model_type,
        )
        crud.set_step_status(db, run_id, "train", StepStatus.success, message=f"model={model_path}")
        crud.update_run_artifacts_and_metrics(db, run_id, artifacts={"model_path": model_path})
        append_log(settings.DATA_ROOT, run_id, f"Step train: done -> {model_path}")

        # Step 3: evaluate
        crud.set_step_status(db, run_id, "evaluate", StepStatus.running)
        append_log(settings.DATA_ROOT, run_id, "Step evaluate: start")
        from pipelines.evaluate import evaluate
        metrics = evaluate(
            processed_path=processed_path,
            model_path=model_path,
            out_dir=dirs["metrics_dir"],
            run_id=run_id,
        )
        metrics_path = str(Path(dirs["metrics_dir"]) / "metrics.json")
        Path(metrics_path).write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        crud.set_step_status(db, run_id, "evaluate", StepStatus.success, message=f"metrics={metrics_path}")
        crud.update_run_artifacts_and_metrics(db, run_id, artifacts={"metrics_path": metrics_path}, metrics=metrics)
        append_log(settings.DATA_ROOT, run_id, f"Step evaluate: done -> {metrics_path}")

        crud.set_run_status(db, run_id, RunStatus.success)
        append_log(settings.DATA_ROOT, run_id, "Run finished: SUCCESS")
        return {"ok": True, "run_id": run_id, "metrics": metrics}

    except Exception as e:
        tb = traceback.format_exc()
        append_log(settings.DATA_ROOT, run_id, f"Run failed: {e}\n{tb}")
        crud.set_step_status(db, run_id, "evaluate", StepStatus.failed, message=str(e))
        crud.set_run_status(db, run_id, RunStatus.failed, error=str(e))
        return {"ok": False, "run_id": run_id, "error": str(e)}
    finally:
        db.close()
