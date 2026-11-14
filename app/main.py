from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import engine, Base
from app.models import sql_models
from app.api.routes.candidates import router as candidates_router
from app.api.routes.dashboard import router as dashboard_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-Agent Orchestration Backend with SQLAlchemy ORM & Qdrant Vector Search",
    version=settings.VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidates_router)
app.include_router(dashboard_router)

@app.get("/", tags=["System Health"])
async def health_check():
    return {
        "system": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "dashboard_url": "http://127.0.0.1:8000/dashboard",
        "status": "online"
    }