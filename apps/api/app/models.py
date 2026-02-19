import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class RunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"
    canceled = "canceled"

class StepStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    skipped = "skipped"

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_path: Mapped[str] = mapped_column(String(800), nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    runs: Mapped[list["Run"]] = relationship(back_populates="dataset")

class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    model_type: Mapped[str] = mapped_column(String(100), default="baseline_sklearn")
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.queued)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    artifacts: Mapped[dict] = mapped_column(JSON, default=dict)   # paths to processed/model/metrics
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)     # scalar metrics summary
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="runs")
    steps: Mapped[list["RunStep"]] = relationship(back_populates="run", cascade="all, delete-orphan")

class RunStep(Base):
    __tablename__ = "run_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # preprocess/train/evaluate
    status: Mapped[StepStatus] = mapped_column(Enum(StepStatus), default=StepStatus.pending)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped["Run"] = relationship(back_populates="steps")
