"""
API des transactions
Endpoints pour créer, lister et gérer les transactions
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Transaction, Account, User, TransactionType, TransactionStatus
from app.schemas.schemas import (
    TransactionCreate, 
    TransactionResponse, 
    TransactionWithFraud,
    FraudAnalysisResult
)
from app.services.auth import get_current_active_user
from app.services.fraud_detection import fraud_service

router = APIRouter(prefix="/transactions", tags=["💳 Transactions"])


@router.post("/", response_model=TransactionWithFraud)
def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle transaction avec analyse de fraude en temps réel 🔒
    """
    # Vérifier que le compte existe et appartient à l'utilisateur
    account = db.query(Account).filter(
        Account.id == transaction.account_id,
        Account.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compte non trouvé"
        )
    
    # Créer la transaction
    db_transaction = Transaction(
        user_id=current_user.id,
        account_id=transaction.account_id,
        transaction_type=TransactionType(transaction.transaction_type.value),
        amount=transaction.amount,
        description=transaction.description,
        recipient_account=transaction.recipient_account,
        recipient_name=transaction.recipient_name,
        category=transaction.category,
        status=TransactionStatus.EN_ATTENTE
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # 🔒 Analyser la transaction avec l'IA de détection de fraude
    fraud_result = fraud_service.analyze_transaction(db, db_transaction, current_user)
    
    # Mettre à jour le score de fraude
    db_transaction.fraud_score = fraud_result["fraud_score"]
    db_transaction.is_fraudulent = fraud_result["is_fraudulent"]
    db_transaction.fraud_reason = fraud_result["fraud_reason"]
    
    # Accepter ou rejeter automatiquement
    if fraud_result["recommendation"] == "reject":
        db_transaction.status = TransactionStatus.REJETEE
    elif fraud_result["recommendation"] == "approve":
        # Vérifier le solde pour les paiements
        if transaction.transaction_type.value in ["paiement", "transfert", "retrait"]:
            if account.balance < transaction.amount:
                db_transaction.status = TransactionStatus.REJETEE
                fraud_result["fraud_reason"] = "Solde insuffisant"
                fraud_result["is_fraudulent"] = True
            else:
                account.balance -= transaction.amount
                db_transaction.status = TransactionStatus.VALIDEE
        else:
            # Encaissement
            account.balance += transaction.amount
            db_transaction.status = TransactionStatus.VALIDEE
    
    db.commit()
    db.refresh(db_transaction)
    
    # Retourner avec l'analyse de fraude
    response = TransactionWithFraud(**{
        "id": db_transaction.id,
        "user_id": db_transaction.user_id,
        "account_id": db_transaction.account_id,
        "transaction_type": db_transaction.transaction_type.value,
        "amount": db_transaction.amount,
        "currency": db_transaction.currency,
        "description": db_transaction.description,
        "status": db_transaction.status.value,
        "fraud_score": db_transaction.fraud_score,
        "is_fraudulent": db_transaction.is_fraudulent,
        "fraud_reason": db_transaction.fraud_reason,
        "recipient_account": db_transaction.recipient_account,
        "recipient_name": db_transaction.recipient_name,
        "category": db_transaction.category,
        "created_at": db_transaction.created_at,
        "validated_at": db_transaction.validated_at,
        "fraud_analysis": fraud_result
    })
    
    return response


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Liste toutes les transactions de l'utilisateur"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        TransactionResponse(
            id=t.id,
            user_id=t.user_id,
            account_id=t.account_id,
            transaction_type=t.transaction_type.value,
            amount=t.amount,
            currency=t.currency,
            description=t.description,
            status=t.status.value,
            fraud_score=t.fraud_score,
            is_fraudulent=bool(t.is_fraudulent),
            fraud_reason=t.fraud_reason,
            recipient_account=t.recipient_account,
            recipient_name=t.recipient_name,
            category=t.category,
            created_at=t.created_at,
            validated_at=t.validated_at
        )
        for t in transactions
    ]


@router.get("/{transaction_id}", response_model=TransactionWithFraud)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les détails d'une transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction non trouvée"
        )
    
    return TransactionWithFraud(
        id=transaction.id,
        user_id=transaction.user_id,
        account_id=transaction.account_id,
        transaction_type=transaction.transaction_type.value,
        amount=transaction.amount,
        currency=transaction.currency,
        description=transaction.description,
        status=transaction.status.value,
        fraud_score=transaction.fraud_score,
        is_fraudulent=bool(transaction.is_fraudulent),
        fraud_reason=transaction.fraud_reason,
        recipient_account=transaction.recipient_account,
        recipient_name=transaction.recipient_name,
        category=transaction.category,
        created_at=transaction.created_at,
        validated_at=transaction.validated_at,
        fraud_analysis={
            "fraud_score": transaction.fraud_score,
            "is_fraudulent": bool(transaction.is_fraudulent),
            "fraud_reason": transaction.fraud_reason
        }
    )


@router.post("/{transaction_id}/analyze", response_model=FraudAnalysisResult)
def analyze_transaction_fraud(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Relance l'analyse de fraude sur une transaction existante"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction non trouvée"
        )
    
    result = fraud_service.analyze_transaction(db, transaction, current_user)
    
    return FraudAnalysisResult(
        transaction_id=transaction.id,
        **result
    )
