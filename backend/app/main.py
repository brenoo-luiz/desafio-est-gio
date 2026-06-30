"""Ponto de entrada da API do Banco (FastAPI)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import accounts

app = FastAPI(
    title="Banco — Desafio Técnico Agilize",
    description="API de operações bancárias (saque e transferência) sobre contas corrente e poupança.",
    version="1.0.0",
)

# Libera o frontend (servido em outra origem/porta) para consumir a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
