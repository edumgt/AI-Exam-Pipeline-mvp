from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app import schemas, crud
from app.workers.tasks import run_pipeline
from app.services.logs import tail_log
from app.config import settings

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=schemas.RunOut)
def create_run(payload: schemas.RunCreate, db: Session = Depends(get_db)):
    # validate dataset
    ds = next((d for d in crud.list_datasets(db, limit=500) if d.id == payload.dataset_id), None)
    if not ds:
        raise HTTPException(status_code=404, detail="dataset not found")
    run = crud.create_run(db, payload.dataset_id, payload.model_type)
    # enqueue
    run_pipeline.delay(run.id)
    # re-fetch to include steps relationship
    run = crud.get_run(db, run.id)
    return run

@router.get("", response_model=list[schemas.RunOut])
def list_runs(db: Session = Depends(get_db)):
    return crud.list_runs(db)

@router.get("/{run_id}", response_model=schemas.RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = crud.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run

@router.get("/{run_id}/logs")
def get_run_logs(run_id: int, lines: int = Query(200, ge=10, le=5000)):
    return {"run_id": run_id, "tail": tail_log(settings.DATA_ROOT, run_id, n=lines)}
