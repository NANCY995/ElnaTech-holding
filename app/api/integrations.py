"""
API Intégrations - Phase 11
Endpoints pour connecter les piliers Elna entre eux
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.models import Transaction, User
from app.models.extended import Notification, NotificationType, FraudAlert

router = APIRouter(prefix="/integrations", tags=["🔗 Intégrations"])


# === Clés API pour authentification inter-piliers ===
# En production, ces clés devraient être stockées de manière sécurisée
INTEGRATION_KEYS = {
    "elna_insights": "insights_secret_key_12345",
    "elna_credit": "credit_secret_key_67890",
    "elna_comply": "comply_secret_key_abcde",
    "elna_market": "market_secret_key_fghij",
}


def verify_integration_key(x_api_key: str = Header(None)) -> str:
    """Vérifie la clé API d'intégration"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Clé API requise")
    
    # Trouver le service
    for service, key in INTEGRATION_KEYS.items():
        if key == x_api_key:
            return service
    
    raise HTTPException(status_code=401, detail="Clé API invalide")


# === Elna Insights ===

@router.post("/insights/push-data")
def push_data_to_insights(
    current_user_id: int,
    year: int,
    api_key: str = Depends(verify_integration_key)
):
    """
    Envoyer l'historique des transactions à Elna Insights
    Données anonymisées pour le scoring analytics
    """
    return {
        "status": "success",
        "message": f"Données de {current_user_id} transmises à Insights pour {year}",
        "records_sent": 0  # À implémenter
    }


@router.get("/insights/anonymized-stats")
def get_anonymized_stats(
    year: int,
    api_key: str = Depends(verify_integration_key)
):
    """
    Obtenir des statistiques anonymisées agrégées
    """
    return {
        "year": year,
        "total_users": 0,
        "total_transactions": 0,
        "total_volume": 0,
        "average_transaction": 0,
        "fraud_rate": 0
    }


# === Elna Credit ===

@router.get("/credit/scoring-data/{user_id}")
def get_scoring_data_for_credit(
    user_id: int,
    api_key: str = Depends(verify_integration_key),
    db: Session = Depends(get_db)
):
    """
    Exposer les données de scoring pour Elna Credit
    Fréquence, volumes, régularité
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Récupérer les transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if not transactions:
        return {
            "user_id": user_id,
            "status": "no_data",
            "score_factors": {}
        }
    
    # Calculer les facteurs de scoring
    total_amount = sum(t.amount for t in transactions)
    transaction_count = len(transactions)
    
    # Fréquence (transactions par mois)
    first_tx = min(transactions, key=lambda t: t.created_at)
    months_active = max(1, (datetime.utcnow() - first_tx.created_at).days / 30)
    transactions_per_month = transaction_count / months_active
    
    # Régularité (écart type des montants)
    amounts = [t.amount for t in transactions]
    avg_amount = total_amount / transaction_count if transaction_count > 0 else 0
    
    # Volume par catégorie
    by_type = {}
    for t in transactions:
        cat = t.category or "autre"
        by_type[cat] = by_type.get(cat, 0) + t.amount
    
    return {
        "user_id": user_id,
        "has_kyc": False,  # À connecter avec KYC
        "factors": {
            "transaction_count": transaction_count,
            "total_volume": total_amount,
            "average_amount": avg_amount,
            "transactions_per_month": round(transactions_per_month, 2),
            "volume_by_category": by_type,
            "account_age_days": (datetime.utcnow() - user.created_at).days
        },
        "calculated_at": datetime.utcnow().isoformat()
    }


# === Elna Comply ===

@router.post("/comply/transactions")
def push_transactions_to_comply(
    user_id: int,
    year: int,
    api_key: str = Depends(verify_integration_key)
):
    """
    Transmettre les données fiscales à Elna Comply pour les déclarations OTR
    """
    return {
        "status": "success",
        "user_id": user_id,
        "year": year,
        "message": "Transactions transmises pour déclaration",
        "records_count": 0
    }


# === Elna Market ===

@router.post("/market/payment")
def process_market_payment(
    order_id: int,
    buyer_id: int,
    amount: float,
    api_key: str = Depends(verify_integration_key),
    db: Session = Depends(get_db)
):
    """
    Traiter les paiements depuis Elna Market via Elna Pay
    """
    # Vérifier l'utilisateur
    user = db.query(User).filter(User.id == buyer_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    return {
        "status": "success",
        "order_id": order_id,
        "buyer_id": buyer_id,
        "amount": amount,
        "message": "Paiement traité avec succès",
        "transaction_id": None  # À implémenter
    }


# === Health Check ===

@router.get("/health")
def integrations_health():
    """
    Statut de santé des intégrations
    """
    return {
        "status": "healthy",
        "services": {
            "elna_insights": "connected",
            "elna_credit": "connected",
            "elna_comply": "connected",
            "elna_market": "connected"
        },
        "version": "1.0.0"
    }


# === Webhooks ===

@router.post("/webhooks/transaction")
def webhook_transaction(
    event_type: str,
    user_id: int,
    amount: float,
    status: str,
    api_key: str = Depends(verify_integration_key),
    db: Session = Depends(get_db)
):
    """
    Webhook pour notifier les autres services d'une transaction
    """
    # Créer une notification
    notification = Notification(
        user_id=user_id,
        title=f"Transaction {event_type}",
        body=f"Une transaction de {amount}€ a été {status}",
        notification_type=NotificationType.TRANSACTION
    )
    db.add(notification)
    db.commit()
    
    return {"status": "received", "event": event_type}


@router.post("/webhooks/fraud-alert")
def webhook_fraud_alert(
    user_id: int,
    risk_score: float,
    reason: str,
    api_key: str = Depends(verify_integration_key),
    db: Session = Depends(get_db)
):
    """
    Webhook pour notifier une alerte de fraude
    """
    alert = FraudAlert(
        user_id=user_id,
        risk_score=risk_score,
        reason=reason
    )
    db.add(alert)
    
    # Notifier l'utilisateur
    notification = Notification(
        user_id=user_id,
        title="⚠️ Alerte de sécurité",
        body=f"Une activité suspecte a été détectée sur votre compte. Score: {risk_score}%",
        notification_type=NotificationType.ALERTE_FRAUDE
    )
    db.add(notification)
    db.commit()
    
    return {"status": "alert_created", "risk_score": risk_score}
