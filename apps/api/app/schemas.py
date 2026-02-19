from datetime import datetime
from pydantic import BaseModel, Field

class DatasetCreate(BaseModel):
    name: str = Field(..., examples=["2026-02-19 batch A"])
    source_path: str = Field(..., examples=["/data/inbound/sample_timeseries.csv"])
    meta: dict = Field(default_factory=dict)

class DatasetOut(BaseModel):
    id: int
    name: str
    source_path: str
    meta: dict
    created_at: datetime

    class Config:
        from_attributes = True

class RunCreate(BaseModel):
    dataset_id: int
    model_type: str = "baseline_sklearn"

class RunStepOut(BaseModel):
    id: int
    name: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    message: str | None

    class Config:
        from_attributes = True

class RunOut(BaseModel):
    id: int
    dataset_id: int
    model_type: str
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    artifacts: dict
    metrics: dict
    error: str | None
    steps: list[RunStepOut] = []

    class Config:
        from_attributes = True
