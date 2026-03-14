"""
Point d'entrée principal de l'application Elna Pay
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.database import Base, engine
from app.models import models  # Import all models
from app.models import market  # Import market models
from app.models import extended  # Import extended models
from app.api import auth, transactions, accounts
from app.api.insights import router as insights_router
from app.api.credit import router as credit_router
from app.api.comply import router as comply_router
from app.api.market import router as market_router
from app.api.integrations import router as integrations_router
from app.api.admin import router as admin_router
from app.api.kyc import router as kyc_router
from app.api.notifications import router as notifications_router
from app.api.mobile_money import router as mobile_money_router
from app.api.webhooks import router as webhooks_router

# Créer les tables
Base.metadata.create_all(bind=engine)

settings = get_settings()

# Chemin absolu vers le répertoire static
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Elna Pay API 💳",
    description="API de paiement unifié avec détection de fraude par IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "http://localhost:8080",
    "https://elnatech.africa",
    "https://*.elnatech.africa",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Inclure les routers
app.include_router(auth.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(insights_router, prefix="/api")
app.include_router(credit_router, prefix="/api")
app.include_router(comply_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(kyc_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(mobile_money_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")


@app.get("/")
def root():
    """Page d'accueil - Interface utilisateur Elna Pay"""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/insights")
def insights_page():
    """Page Elna Insights"""
    return FileResponse(str(STATIC_DIR / "insights.html"))


@app.get("/credit")
def credit_page():
    """Page Elna Credit"""
    return FileResponse(str(STATIC_DIR / "credit.html"))


@app.get("/comply")
def comply_page():
    """Page Elna Comply"""
    return FileResponse(str(STATIC_DIR / "comply.html"))


@app.get("/market")
def market_page():
    """Page Elna Market"""
    return FileResponse(str(STATIC_DIR / "market.html"))


@app.get("/admin")
def admin_page():
    """Page Admin Elna"""
    return FileResponse(str(STATIC_DIR / "admin.html"))


@app.get("/health")
def health_check():
    """Vérification de l'état de l'API"""
    return {"status": "healthy", "service": "Elna Pay"}
