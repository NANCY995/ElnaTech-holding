"""
API Elna Credit
Endpoints pour le scoring et les offres de crédit
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User
from app.services.auth import get_current_active_user
from app.services.credit.service import credit_service

router = APIRouter(prefix="/credit", tags=["💰 Credit"])


@router.get("/score")
def get_credit_score(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calcule le score de credit (0-1000)"""
    return credit_service.calculate_credit_score(db, current_user.id)


@router.get("/offres")
def get_loan_offers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retourne les offres de prêt personnalisées"""
    return credit_service.get_loan_offers(db, current_user.id)


@router.get("/simuler")
def simulate_loan(
    amount: float = Query(gt=0),
    months: int = Query(gt=0, le=60),
    rate: float = Query(ge=0, le=0.3),
    current_user: User = Depends(get_current_active_user)
):
    """Simule un prêt"""
    return credit_service.simulate_loan(amount, months, rate)


@router.get("/rapport")
def get_credit_report(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Génère un rapport de credit complet"""
    return credit_service.get_credit_report(db, current_user.id)
