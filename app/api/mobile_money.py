"""
API Mobile Money - Opérateurs
Phase 3 - Intégration CinetPay, Kkiapay, Flooz, T-Money
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.models import User, Account, Transaction
from app.models.extended import Operator
from app.services.auth import get_current_active_user

router = APIRouter(prefix="/mobile-money", tags=["📱 Mobile Money"])


# === Schemas ===

class CashInRequest(BaseModel):
    operator: str  # flooz, tmoney, orange
    phone_number: str
    amount: float
    provider: str = "internal"  # cinetpay, kkiapay, internal


class CashOutRequest(BaseModel):
    operator: str
    phone_number: str
    amount: float


class OperatorResponse(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    cash_in_fee_percent: float
    cash_out_fee_percent: float


# === Endpoints ===

@router.get("/operators")
def list_operators(db: Session = Depends(get_db)):
    """Liste des opérateurs disponibles"""
    operators = db.query(Operator).filter(Operator.is_active == True).all()
    
    return [
        {
            "id": o.id,
            "name": o.name,
            "code": o.code,
            "is_active": o.is_active,
            "fees": {
                "cash_in": f"{o.cash_in_fee_percent}%",
                "cash_out": f"{o.cash_out_fee_percent}%"
            }
        }
        for o in operators
    ]


@router.post("/cash-in")
def cash_in(
    request: CashInRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Déposer de l'argent depuis Mobile Money vers Elna Pay
    Cash-in (flooz/tmoney/orange -> compte Elna)
    """
    # Vérifier l'opérateur
    operator = db.query(Operator).filter(
        Operator.code == request.operator,
        Operator.is_active == True
    ).first()
    
    if not operator:
        raise HTTPException(status_code=400, detail="Opérateur non disponible")
    
    # Calculer les frais
    fee = request.amount * (operator.cash_in_fee_percent / 100)
    net_amount = request.amount - fee
    
    # Créer la transaction
    # En production: appeler l'API du provider (CinetPay/Kkiapay)
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type="encaissement",
        amount=net_amount,
        description=f"Cash-in {operator.name} depuis {request.phone_number}",
        category="mobile_money",
        status="en_attente"
    )
    db.add(transaction)
    
    # Créer une notification
    from app.models.extended import Notification, NotificationType
    notification = Notification(
        user_id=current_user.id,
        title="Dépôt en cours",
        body=f"Votre dépôt de {request.amount}€ via {operator.name} est en cours de traitement",
        notification_type=NotificationType.TRANSACTION
    )
    db.add(notification)
    db.commit()
    db.refresh(transaction)
    
    # Simulation: approuver après quelques secondes
    # En production: attendre webhook du provider
    
    return {
        "status": "pending",
        "transaction_id": transaction.id,
        "amount": request.amount,
        "fee": fee,
        "net_amount": net_amount,
        "operator": operator.name,
        "message": "Dépôt en attente de confirmation"
    }


@router.post("/cash-out")
def cash_out(
    request: CashOutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retirer de l'argent vers Mobile Money
    Cash-out (compte Elna -> flooz/tmoney/orange)
    """
    # Vérifier l'opérateur
    operator = db.query(Operator).filter(
        Operator.code == request.operator,
        Operator.is_active == True
    ).first()
    
    if not operator:
        raise HTTPException(status_code=400, detail="Opérateur non disponible")
    
    # Calculer les frais
    fee = request.amount * (operator.cash_out_fee_percent / 100)
    total = request.amount + fee
    
    # Vérifier le solde
    account = db.query(Account).filter(
        Account.user_id == current_user.id
    ).first()
    
    if not account or account.balance < total:
        raise HTTPException(status_code=400, detail="Solde insuffisant")
    
    # Débiter le compte
    account.balance -= total
    
    # Créer la transaction
    transaction = Transaction(
        user_id=current_user.id,
        account_id=account.id,
        transaction_type="retrait",
        amount=request.amount,
        description=f"Cash-out vers {operator.name} {request.phone_number}",
        category="mobile_money",
        status="en_attente"
    )
    db.add(transaction)
    
    # Notification
    from app.models.extended import Notification, NotificationType
    notification = Notification(
        user_id=current_user.id,
        title="Retrait en cours",
        body=f"Votre retrait de {request.amount}€ vers {operator.name} est en cours",
        notification_type=NotificationType.TRANSACTION
    )
    db.add(notification)
    db.commit()
    
    return {
        "status": "pending",
        "transaction_id": transaction.id,
        "amount": request.amount,
        "fee": fee,
        "total_deducted": total,
        "operator": operator.name,
        "phone": request.phone_number,
        "message": "Retrait en attente de confirmation"
    }


@router.get("/fees/{operator}")
def get_operator_fees(
    operator: str,
    amount: float,
    operation: str,  # cash_in or cash_out
    db: Session = Depends(get_db)
):
    """Calculer les frais pour une opération"""
    op = db.query(Operator).filter(
        Operator.code == operator,
        Operator.is_active == True
    ).first()
    
    if not op:
        raise HTTPException(status_code=404, detail="Opérateur non trouvé")
    
    if operation == "cash_in":
        fee_percent = op.cash_in_fee_percent
    elif operation == "cash_out":
        fee_percent = op.cash_out_fee_percent
    else:
        raise HTTPException(status_code=400, detail="Opération invalide")
    
    fee = amount * (fee_percent / 100)
    net = amount - fee if operation == "cash_in" else amount
    
    return {
        "operator": op.name,
        "operation": operation,
        "amount": amount,
        "fee_percent": fee_percent,
        "fee": round(fee, 2),
        "net_amount": round(net, 2),
        "total": round(amount + fee, 2) if operation == "cash_out" else round(net, 2)
    }


@router.post("/webhooks/{provider}")
def mobile_money_webhook(
    provider: str,
    status: str,
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Webhook pour les notifications de paiement Mobile Money
    En production: vérifier signature du provider
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    # Mettre à jour le statut
    if status == "success":
        transaction.status = "validee"
        
        # Créditer le compte si cash-in
        if transaction.transaction_type == "encaissement":
            account = db.query(Account).filter(Account.id == transaction.account_id).first()
            if account:
                account.balance += transaction.amount
        
        message = "Transaction confirmée"
    elif status == "failed":
        transaction.status = "rejetée"
        message = "Transaction échouée"
    else:
        message = "Statut inconnu"
    
    db.commit()
    
    return {"status": "processed", "message": message}
