from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from . import models

def create_dataset(db: Session, name: str, source_path: str, meta: dict):
    ds = models.Dataset(name=name, source_path=source_path, meta=meta or {})
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds

def list_datasets(db: Session, limit: int = 100):
    stmt = select(models.Dataset).order_by(desc(models.Dataset.id)).limit(limit)
    return list(db.scalars(stmt).all())

def create_run(db: Session, dataset_id: int, model_type: str):
    run = models.Run(dataset_id=dataset_id, model_type=model_type, status=models.RunStatus.queued)
    db.add(run)
    db.commit()
    db.refresh(run)

    # init steps
    for step_name in ["preprocess", "train", "evaluate"]:
        st = models.RunStep(run_id=run.id, name=step_name, status=models.StepStatus.pending)
        db.add(st)
    db.commit()
    db.refresh(run)
    return run

def get_run(db: Session, run_id: int):
    stmt = select(models.Run).where(models.Run.id == run_id)
    run = db.scalars(stmt).first()
    return run

def list_runs(db: Session, limit: int = 200):
    stmt = select(models.Run).order_by(desc(models.Run.id)).limit(limit)
    return list(db.scalars(stmt).all())

def set_run_status(db: Session, run_id: int, status: models.RunStatus, *, error: str | None = None):
    run = get_run(db, run_id)
    if not run:
        return None
    run.status = status
    if status == models.RunStatus.running:
        run.started_at = datetime.utcnow()
    if status in (models.RunStatus.success, models.RunStatus.failed, models.RunStatus.canceled):
        run.finished_at = datetime.utcnow()
    if error:
        run.error = error
    db.commit()
    db.refresh(run)
    return run

def set_step_status(db: Session, run_id: int, step_name: str, status: models.StepStatus, message: str | None = None):
    stmt = select(models.RunStep).where(models.RunStep.run_id == run_id, models.RunStep.name == step_name)
    step = db.scalars(stmt).first()
    if not step:
        return None
    step.status = status
    if status == models.StepStatus.running:
        step.started_at = datetime.utcnow()
    if status in (models.StepStatus.success, models.StepStatus.failed, models.StepStatus.skipped):
        step.finished_at = datetime.utcnow()
    if message is not None:
        step.message = message
    db.commit()
    db.refresh(step)
    return step

def update_run_artifacts_and_metrics(db: Session, run_id: int, artifacts: dict | None = None, metrics: dict | None = None):
    run = get_run(db, run_id)
    if not run:
        return None
    if artifacts:
        run.artifacts = {**(run.artifacts or {}), **artifacts}
    if metrics:
        run.metrics = {**(run.metrics or {}), **metrics}
    db.commit()
    db.refresh(run)
    return run
