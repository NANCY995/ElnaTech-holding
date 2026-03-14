"""
API Webhooks
Phase 11 - Webhooks pour événements externes
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import hmac
import hashlib
import json

from app.core.database import get_db
from app.models.models import Transaction
from app.models.extended import FraudAlert, Notification, NotificationType

router = APIRouter(prefix="/webhooks", tags=["🔗 Webhooks"])


class WebhookPayload(BaseModel):
    event: str
    data: dict


def verify_webhook_signature(
    payload: str,
    signature: Optional[str],
    secret: str = "webhook-secret-key"
) -> bool:
    """
    Vérifie la signature du webhook
    En production: utiliser le secret du provider
    """
    if not signature:
        return False  # Pour le développement, autoriser sans signature
    
    # Calculer la signature attendue
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


@router.post("/payment/{provider}")
def payment_webhook(
    provider: str,
    payload: WebhookPayload,
    x_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook pour les événements de paiement
    Providers: cinetpay, kkiapay, stripe, paypal
    """
    # En production: vérifier la signature
    # verify_webhook_signature(payload.json(), x_signature)
    
    event = payload.event
    data = payload.data
    
    if event == "payment.success":
        # Confirmer la transaction
        tx_id = data.get("transaction_id")
        if tx_id:
            tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
            if tx:
                tx.status = "validee"
                
                # Notifier l'utilisateur
                notification = Notification(
                    user_id=tx.user_id,
                    title="Paiement confirmé",
                    body=f"Votre paiement de {tx.amount}€ a été confirmé",
                    notification_type=NotificationType.TRANSACTION
                )
                db.add(notification)
                db.commit()
                
                return {"status": "processed"}
    
    elif event == "payment.failed":
        tx_id = data.get("transaction_id")
        if tx_id:
            tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
            if tx:
                tx.status = "rejetée"
                db.commit()
                
                return {"status": "processed"}
    
    return {"status": "ignored"}


@router.post("/fraud-alert")
def fraud_webhook(
    payload: WebhookPayload,
    x_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook pour les alertes fraude externes
    """
    event = payload.event
    data = payload.data
    
    if event == "fraud.detected":
        user_id = data.get("user_id")
        if user_id:
            alert = FraudAlert(
                user_id=user_id,
                risk_score=data.get("risk_score", 50),
                reason=data.get("reason", "Alerte externe"),
                source="external_api"
            )
            db.add(alert)
            db.commit()
            
            #Notifier l'admin
            notification = Notification(
                user_id=user_id,
                title="Alerte de sécurité",
                body="Une activité suspecte a été détectée sur votre compte",
                notification_type=NotificationType.SECURITY
            )
            db.add(notification)
            db.commit()
            
            return {"status": "processed"}
    
    return {"status": "ignored"}


@router.post("/kyc/{provider}")
def kyc_webhook(
    provider: str,
    payload: WebhookPayload,
    db: Session = Depends(get_db)
):
    """
    Webhook pour les événements KYC
    Providers: smile_identity, onfido, sumsub
    """
    event = payload.event
    data = payload.data
    
    if event == "kyc.approved":
        user_id = data.get("user_id")
        # Mettre à jour le KYC
        # kyc = db.query(KYCRecord).filter(KYCRecord.user_id == user_id).first()
        # if kyc: kyc.status = KYCStatus.VERIFIE
        return {"status": "processed"}
    
    elif event == "kyc.rejected":
        user_id = data.get("user_id")
        reason = data.get("reason")
        # Mettre à jour le KYC
        return {"status": "processed"}
    
    return {"status": "ignored"}
