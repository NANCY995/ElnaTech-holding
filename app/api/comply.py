"""
API Elna Comply
Endpoints pour les declarations fiscales
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User
from app.services.auth import get_current_active_user
from app.services.comply.service import comply_service

router = APIRouter(prefix="/comply", tags=["📋 Comply"])


@router.get("/fiscal")
def get_tax_summary(
    year: int = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Résumé fiscal pour l'année"""
    return comply_service.get_tax_summary(db, current_user.id, year)


@router.get("/declaration")
def generate_declaration(
    year: int = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Génère une déclaration de revenus"""
    return comply_service.generate_declaration(db, current_user.id, year)


@router.get("/tva")
def get_tva_summary(
    year: int = Query(default=None),
    quarter: int = Query(default=None, ge=1, le=4),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Résumé TVA"""
    return comply_service.get_tva_summary(db, current_user.id, year, quarter)


@router.get("/social")
def get_social_contributions(
    year: int = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cotisations sociales estimées"""
    return comply_service.get_social_contributions(db, current_user.id, year)


@router.get("/rapport")
def get_annual_report(
    year: int = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rapport annuel complet"""
    return comply_service.get_annual_report(db, current_user.id, year)
