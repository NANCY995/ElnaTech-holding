"""
Service KYC - Vérification d'Identité
Phase 8 - Intégration vérification d'identité
"""
import random
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.extended import KYCRecord, KYCStatus, DocumentType, Notification, NotificationType
from app.models.models import User


class KYCService:
    """
    Service de vérification d'identité (KYC)
    En production: intégration avec Smile Identity, Onfido, etc.
    """
    
    # Limites par niveau KYC
    LIMITS = {
        KYCStatus.NON_INITIE: {"daily": 50000, "single": 10000},
        KYCStatus.EN_COURS: {"daily": 100000, "single": 50000},
        KYCStatus.EN_ATTENTE: {"daily": 100000, "single": 50000},
        KYCStatus.VERIFIE: {"daily": 500000, "single": 200000},
        KYCStatus.REJETE: {"daily": 50000, "single": 10000},
    }
    
    def initiate_kyc(
        self,
        db: Session,
        user_id: int,
        document_type: str,
        document_number: str
    ) -> KYCRecord:
        """Initie le processus KYC"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        existing = db.query(KYCRecord).filter(KYCRecord.user_id == user_id).first()
        if existing:
            if existing.status == KYCStatus.VERIFIE:
                raise ValueError("KYC déjà vérifié")
            if existing.status == KYCStatus.EN_COURS:
                raise ValueError("KYC déjà en cours")
        
        kyc = KYCRecord(
            user_id=user_id,
            document_type=DocumentType(document_type),
            document_number=document_number,
            status=KYCStatus.EN_COURS
        )
        db.add(kyc)
        
        notification = Notification(
            user_id=user_id,
            title="KYC en cours",
            body="Votre vérification d'identité est en cours de traitement",
            notification_type=NotificationType.KYC
        )
        db.add(notification)
        db.commit()
        db.refresh(kyc)
        
        return kyc
    
    def upload_document(
        self,
        db: Session,
        user_id: int,
        document_front_url: str,
        document_back_url: str = None
    ) -> KYCRecord:
        """Upload les photos du document"""
        kyc = db.query(KYCRecord).filter(
            KYCRecord.user_id == user_id,
            KYCRecord.status == KYCStatus.EN_COURS
        ).first()
        
        if not kyc:
            raise ValueError("Aucun KYC en cours")
        
        kyc.document_front_url = document_front_url
        kyc.document_back_url = document_back_url
        kyc.status = KYCStatus.EN_ATTENTE
        
        db.commit()
        db.refresh(kyc)
        
        return kyc
    
    def upload_selfie(
        self,
        db: Session,
        user_id: int,
        selfie_url: str,
        liveness_verified: bool = False
    ) -> KYCRecord:
        """Upload le selfie de vérification"""
        kyc = db.query(KYCRecord).filter(
            KYCRecord.user_id == user_id,
            KYCRecord.status == KYCStatus.EN_ATTENTE
        ).first()
        
        if not kyc:
            raise ValueError("Aucun KYC en attente")
        
        kyc.selfie_url = selfie_url
        kyc.liveness_verified = liveness_verified
        
        self._verify_kyc(db, kyc)
        
        return kyc
    
    def _verify_kyc(self, db: Session, kyc: KYCRecord):
        """Vérifie le KYC (simulation)"""
        if kyc.document_number and len(kyc.document_number) >= 5:
            kyc.status = KYCStatus.VERIFIE
            kyc.verified_at = datetime.utcnow()
            kyc.provider = "internal"
            
            notification = Notification(
                user_id=kyc.user_id,
                title="KYC vérifié",
                body="Votre identité a été vérifiée. Limites augmentées.",
                notification_type=NotificationType.KYC
            )
            db.add(notification)
        else:
            kyc.status = KYCStatus.REJETE
            kyc.rejection_reason = "Document invalide"
        
        db.commit()
    
    def get_kyc_status(self, db: Session, user_id: int) -> Dict:
        """Retourne le statut KYC"""
        kyc = db.query(KYCRecord).filter(KYCRecord.user_id == user_id).first()
        
        if not kyc:
            return {
                "status": KYCStatus.NON_INITIE.value,
                "level": "basic",
                "limits": self.LIMITS[KYCStatus.NON_INITIE]
            }
        
        return {
            "status": kyc.status.value,
            "document_type": kyc.document_type.value if kyc.document_type else None,
            "verified_at": kyc.verified_at.isoformat() if kyc.verified_at else None,
            "level": self._get_kyc_level(kyc.status),
            "limits": self.LIMITS.get(kyc.status, self.LIMITS[KYCStatus.NON_INITIE])
        }
    
    def _get_kyc_level(self, status: KYCStatus) -> str:
        levels = {
            KYCStatus.NON_INITIE: "basic",
            KYCStatus.EN_COURS: "intermediate",
            KYCStatus.EN_ATTENTE: "intermediate",
            KYCStatus.VERIFIE: "full",
            KYCStatus.REJETE: "basic",
        }
        return levels.get(status, "basic")
    
    def check_transaction_limits(
        self,
        db: Session,
        user_id: int,
        amount: float
    ) -> Dict:
        """Vérifie les limites KYC"""
        kyc_info = self.get_kyc_status(db, user_id)
        limits = kyc_info["limits"]
        
        if amount > limits["single"]:
            return {
                "allowed": False,
                "reason": f"Montant max: {limits['single']}fcfa",
                "required_level": "full"
            }
        
        return {"allowed": True}


# Instance globale
kyc_service = KYCService()
