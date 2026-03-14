"""
API des comptes bancaires
Endpoints pour créer et gérer les comptes
"""
import random
import string
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Account, User
from app.schemas.schemas import AccountCreate, AccountResponse
from app.services.auth import get_current_active_user

router = APIRouter(prefix="/accounts", tags=["🏦 Comptes"])


def generate_account_number() -> str:
    """Génère un numéro de compte unique (format IBAN simplifié)"""
    # FR76 + 13 chiffres aléatoires
    digits = ''.join(random.choices(string.digits, k=13))
    return f"FR76{digits}"


@router.post("/", response_model=AccountResponse)
def create_account(
    account: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crée un nouveau compte bancaire"""
    account_number = generate_account_number()
    
    new_account = Account(
        user_id=current_user.id,
        account_number=account_number,
        account_type=account.account_type,
        currency=account.currency,
        balance=0.0
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return new_account


@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Liste tous les comptes de l'utilisateur"""
    accounts = db.query(Account).filter(
        Account.user_id == current_user.id,
        Account.is_active == True
    ).all()
    
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les détails d'un compte"""
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compte non trouvé"
        )
    
    return account


@router.get("/{account_id}/balance")
def get_balance(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère le solde d'un compte"""
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compte non trouvé"
        )
    
    return {
        "account_id": account.id,
        "account_number": account.account_number,
        "balance": account.balance,
        "currency": account.currency
    }
