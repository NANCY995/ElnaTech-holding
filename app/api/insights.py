"""
API Elna Insights
Endpoints pour les analytics et business intelligence
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.models import User
from app.services.auth import get_current_active_user
from app.services.insights.service import insights_service

router = APIRouter(prefix="/insights", tags=["📊 Insights"])


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Résumé du tableau de bord"""
    return insights_service.get_dashboard_summary(db, current_user.id)


@router.get("/revenus")
def get_revenus(
    days: int = Query(default=30, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revenus par catégorie"""
    return insights_service.get_revenue_by_category(db, current_user.id, days)


@router.get("/depenses")
def get_depenses(
    days: int = Query(default=30, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dépenses par catégorie"""
    return insights_service.get_expenses_by_category(db, current_user.id, days)


@router.get("/cashflow")
def get_cashflow(
    days: int = Query(default=30, le=365),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Flux de trésorerie quotidien"""
    return insights_service.get_daily_cashflow(db, current_user.id, days)


@router.get("/clients")
def get_clients(
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Meilleurs clients"""
    return insights_service.get_top_clients(db, current_user.id, limit)


@router.get("/fournisseurs")
def get_fournisseurs(
    limit: int = Query(default=10, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Principaux fournisseurs"""
    return insights_service.get_top_suppliers(db, current_user.id, limit)


@router.get("/mensuel")
def get_mensuel(
    months: int = Query(default=6, le=24),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Comparaison mensuelle"""
    return insights_service.get_monthly_comparison(db, current_user.id, months)


@router.get("/fraude")
def get_fraude_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Statistiques de fraude"""
    return insights_service.get_fraud_statistics(db, current_user.id)


@router.get("/sante")
def get_business_health(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Score de santé financière"""
    return insights_service.get_business_health_score(db, current_user.id)
