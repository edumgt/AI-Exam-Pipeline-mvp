from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import schemas, crud

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.post("", response_model=schemas.DatasetOut)
def create_dataset(payload: schemas.DatasetCreate, db: Session = Depends(get_db)):
    # MVP: only validate path existence inside container
    import os
    if not os.path.exists(payload.source_path):
        raise HTTPException(status_code=400, detail=f"source_path not found: {payload.source_path}")
    return crud.create_dataset(db, payload.name, payload.source_path, payload.meta)

@router.get("", response_model=list[schemas.DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return crud.list_datasets(db)
