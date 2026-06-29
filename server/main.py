from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from app.routes import analyze, health, improve, rag

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(improve.router)
app.include_router(health.router)
app.include_router(rag.router)
