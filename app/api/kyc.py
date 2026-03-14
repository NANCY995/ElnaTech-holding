"""
API KYC - Vérification d'Identité
Phase 8 - Endpoints pour le KYC
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import User
from app.services.auth import get_current_active_user
from app.services.kyc.service import kyc_service

router = APIRouter(prefix="/kyc", tags=["🪪 KYC"])


class KYCInitiateRequest(BaseModel):
    document_type: str
    document_number: str


class KYCDocumentUpload(BaseModel):
    document_front_url: str
    document_back_url: str = None


class KYCSelfieUpload(BaseModel):
    selfie_url: str
    liveness_verified: bool = False


@router.post("/initiate")
def initiate_kyc(
    request: KYCInitiateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initie le processus KYC"""
    try:
        kyc = kyc_service.initiate_kyc(
            db=db,
            user_id=current_user.id,
            document_type=request.document_type,
            document_number=request.document_number
        )
        return {
            "status": "initiated",
            "kyc_id": kyc.id,
            "message": "KYC initiated. Please upload your document."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/document")
def upload_document(
    request: KYCDocumentUpload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload les photos du document d'identité"""
    try:
        kyc = kyc_service.upload_document(
            db=db,
            user_id=current_user.id,
            document_front_url=request.document_front_url,
            document_back_url=request.document_back_url
        )
        return {
            "status": "uploaded",
            "message": "Document uploaded. Please upload your selfie."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/selfie")
def upload_selfie(
    request: KYCSelfieUpload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload le selfie de vérification"""
    try:
        kyc = kyc_service.upload_selfie(
            db=db,
            user_id=current_user.id,
            selfie_url=request.selfie_url,
            liveness_verified=request.liveness_verified
        )
        return {
            "status": kyc.status.value,
            "message": "Vérification en cours" if kyc.status.value != "verifie" else "KYC vérifié avec succès!"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
def get_kyc_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère le statut KYC"""
    return kyc_service.get_kyc_status(db, current_user.id)


@router.get("/limits/{amount}")
def check_limits(
    amount: float,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Vérifie les limites pour un montant"""
    return kyc_service.check_transaction_limits(db, current_user.id, amount)
