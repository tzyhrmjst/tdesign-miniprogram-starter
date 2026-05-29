from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.alerts import router as alerts_router
from app.api.auth import router as auth_router
from app.api.gold import router as gold_router
from app.db.database import init_db
from app.services.scheduler_service import start_scheduler, stop_scheduler

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Gold Alert API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gold_router)
app.include_router(alerts_router)
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"success": True, "data": "ok"}
