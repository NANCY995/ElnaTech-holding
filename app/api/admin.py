"""
API Admin - Gestion du panneau administrateur
Phase 10 - Tableau de bord administrateur
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import User, Transaction, Account
from app.models.extended import FraudAlert, AuditLog, AdminUser, Notification, KYCRecord, KYCStatus, AdminRole, AuditAction

router = APIRouter(prefix="/admin", tags=["🏛️ Admin"])


# === Schemas Admin ===

class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_transactions: int
    total_volume: float
    pending_kyc: int
    open_fraud_alerts: int
    revenue_today: float


class UserManagement(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    is_seller: bool
    created_at: datetime


class TransactionFilter(BaseModel):
    id: int
    user_id: int
    username: str
    amount: float
    transaction_type: str
    status: str
    created_at: datetime


# === Middleware Admin (simplifié) ===

def get_current_admin(admin_id: int = Query(1)):  # Simplifié pour le POC
    """Vérifie que l'utilisateur est admin"""
    # En production: vérifier JWT et rôle
    return {"id": admin_id, "role": "super_admin"}


# === Dashboard ===

@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """KPIs en temps réel pour le dashboard"""
    
    # Utilisateurs
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Transactions
    total_transactions = db.query(Transaction).count()
    total_volume = db.query(func.sum(Transaction.amount)).scalar() or 0
    
    # KYC en attente
    pending_kyc = db.query(KYCRecord).filter(
        KYCRecord.status == KYCStatus.EN_COURS
    ).count()
    
    # Alertes fraude ouvertes
    open_alerts = db.query(FraudAlert).filter(
        FraudAlert.is_resolved == False
    ).count()
    
    # Revenus aujourd'hui
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    revenue_today = db.query(func.sum(Transaction.amount)).filter(
        Transaction.created_at >= today,
        Transaction.transaction_type.in_(["encaissement", "paiement"])
    ).scalar() or 0
    
    return DashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_transactions=total_transactions,
        total_volume=round(total_volume, 2),
        pending_kyc=pending_kyc,
        open_fraud_alerts=open_alerts,
        revenue_today=round(revenue_today, 2)
    )


# === Gestion Utilisateurs ===

@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Liste des utilisateurs avec filtres"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.email.contains(search)) | 
            (User.username.contains(search)) |
            (User.full_name.contains(search))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset((page-1)*limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "full_name": u.full_name,
                "is_active": bool(u.is_active),
                "is_seller": bool(u.is_seller),
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]
    }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Détail d'un utilisateur"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Comptes
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    
    # Transactions récentes
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(desc(Transaction.created_at)).limit(10).all()
    
    # KYC
    kyc = db.query(KYCRecord).filter(KYCRecord.user_id == user_id).first()
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": bool(user.is_active),
            "is_seller": bool(user.is_seller),
            "shop_name": user.shop_name,
            "created_at": user.created_at.isoformat()
        },
        "accounts": [
            {
                "id": a.id,
                "account_number": a.account_number,
                "balance": a.balance,
                "currency": a.currency
            }
            for a in accounts
        ],
        "recent_transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ],
        "kyc": {
            "status": kyc.status.value if kyc else "non_initie",
            "document_type": kyc.document_type.value if kyc and kyc.document_type else None
        } if kyc else None
    }


@router.post("/users/{user_id}/suspend")
def suspend_user(
    user_id: int,
    reason: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Suspendre un utilisateur"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user.is_active = False
    
    # Log d'audit
    audit = AuditLog(
        admin_id=admin["id"],
        action=AuditAction.BLOCK,
        entity_type="user",
        entity_id=user_id,
        description=f"Suspension: {reason}"
    )
    db.add(audit)
    db.commit()
    
    return {"status": "suspended", "user_id": user_id}


@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Réactiver un utilisateur"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    user.is_active = True
    
    audit = AuditLog(
        admin_id=admin["id"],
        action=AuditAction.UNBLOCK,
        entity_type="user",
        entity_id=user_id,
        description="Réactivation du compte"
    )
    db.add(audit)
    db.commit()
    
    return {"status": "activated", "user_id": user_id}


# === Monitoring Transactions ===

@router.get("/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    status: Optional[str] = None,
    transaction_type: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Liste des transactions avec filtres avancés"""
    query = db.query(Transaction).join(User)
    
    if status:
        query = query.filter(Transaction.status == status)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if min_amount:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount:
        query = query.filter(Transaction.amount <= max_amount)
    
    total = query.count()
    transactions = query.order_by(desc(Transaction.created_at)).offset((page-1)*limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "transactions": [
            {
                "id": t.id,
                "user_id": t.user_id,
                "username": t.user.username,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
    }


# === Alertes Fraude ===

@router.get("/fraud-alerts")
def list_fraud_alerts(
    resolved: Optional[bool] = None,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Liste des alertes de fraude"""
    query = db.query(FraudAlert)
    
    if resolved is not None:
        query = query.filter(FraudAlert.is_resolved == resolved)
    
    alerts = query.order_by(desc(FraudAlert.created_at)).limit(limit).all()
    
    return {
        "total": len(alerts),
        "alerts": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "risk_score": a.risk_score,
                "reason": a.reason,
                "is_resolved": a.is_resolved,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ]
    }


@router.post("/fraud-alerts/{alert_id}/resolve")
def resolve_fraud_alert(
    alert_id: int,
    resolution_notes: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Résoudre une alerte de fraude"""
    alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    
    alert.is_resolved = True
    alert.resolved_by = admin["id"]
    alert.resolution_notes = resolution_notes
    alert.resolved_at = datetime.utcnow()
    
    audit = AuditLog(
        admin_id=admin["id"],
        action=AuditAction.UPDATE,
        entity_type="fraud_alert",
        entity_id=alert_id,
        description=f"Résolution: {resolution_notes}"
    )
    db.add(audit)
    db.commit()
    
    return {"status": "resolved", "alert_id": alert_id}


# === Logs d'Audit ===

@router.get("/audit-logs")
def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Liste des logs d'audit"""
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    total = query.count()
    logs = query.order_by(desc(AuditLog.created_at)).offset((page-1)*limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "logs": [
            {
                "id": l.id,
                "admin_id": l.admin_id,
                "action": l.action.value,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "description": l.description,
                "created_at": l.created_at.isoformat()
            }
            for l in logs
        ]
    }


# === Configuration ===

@router.get("/system/config")
def get_system_config(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Configuration système"""
    return {
        "limits": {
            "transaction_daily_max": 100000,
            "withdrawal_max": 50000,
            "kyc_pending_days": 7
        },
        "fees": {
            "transfer_percent": 1.0,
            "withdrawal_percent": 1.5
        },
        "features": {
            "kyc_enabled": True,
            "fraud_detection_enabled": True,
            "market_enabled": True
        }
    }
