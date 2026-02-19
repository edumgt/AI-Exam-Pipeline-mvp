from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import engine
from app.models import Base
from app.routes.health import router as health_router
from app.routes.datasets import router as datasets_router
from app.routes.runs import router as runs_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Exam AI Pipeline MVP", openapi_url="/api/openapi.json", docs_url="/api/docs", redoc_url="/api/redoc")

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount under /api
api = FastAPI(title="API")
api.include_router(health_router)
api.include_router(datasets_router)
api.include_router(runs_router)

app.mount("/api", api)

@app.get("/")
def root():
    return {"ok": True, "service": "exam-ai-pipeline-mvp", "docs": "/api/docs"}
