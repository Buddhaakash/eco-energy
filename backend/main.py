from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import (
    datasets, analysis, anomalies, recommendations, settings, chat, report, bill,
)

app = FastAPI(title="EcoEnergy API", version="1.0.0")

# Wide-open CORS is fine for a hackathon demo (single-user, no auth yet).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(analysis.router)
app.include_router(anomalies.router)
app.include_router(recommendations.router)
app.include_router(settings.router)
app.include_router(chat.router)
app.include_router(report.router)
app.include_router(bill.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "EcoEnergy API", "docs": "/docs"}
