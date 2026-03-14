"""
Modèles supplémentaires pour Elna Pay
Notifications, Audit Logs, KYC, Admin
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Types de notifications"""
    TRANSACTION = "transaction"
    ALERTE_FRAUDE = "alerte_fraude"
    KYC = "kyc"
    SYSTEM = "system"
    MARKET = "market"


class Notification(Base):
    """Modèle Notification"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    notification_type = Column(SQLEnum(NotificationType), default=NotificationType.SYSTEM)
    is_read = Column(Boolean, default=False)
    
    # Données additionnelles en JSON
    extra_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    user = relationship("User")


class KYCStatus(str, enum.Enum):
    """Statut KYC"""
    NON_INITIE = "non_initie"
    EN_COURS = "en_cours"
    EN_ATTENTE = "en_attente"
    VERIFIE = "verifie"
    REJETE = "rejete"


class DocumentType(str, enum.Enum):
    """Types de documents"""
    CNI = "cni"
    PASSEPORT = "passeport"
    PERMIS = "permis"


class KYCRecord(Base):
    """Modèle KYC - Vérification d'identité"""
    __tablename__ = "kyc_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Document
    document_type = Column(SQLEnum(DocumentType))
    document_number = Column(String)
    document_front_url = Column(String, nullable=True)
    document_back_url = Column(String, nullable=True)
    
    # Selfie
    selfie_url = Column(String, nullable=True)
    liveness_verified = Column(Boolean, default=False)
    
    # Statut
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.NON_INITIE)
    verified_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)
    
    # Métadonnées
    provider = Column(String, default="internal")  # Smile Identity, etc.
    external_id = Column(String, nullable=True)  # ID externe
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    user = relationship("User")


class AdminRole(str, enum.Enum):
    """Rôles admin"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    SUPPORT = "support"


class AdminUser(Base):
    """Modèle Administrateur"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(AdminRole), default=AdminRole.SUPPORT)
    is_active = Column(Boolean, default=True)
    
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditAction(str, enum.Enum):
    """Actions d'audit"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    BLOCK = "block"
    UNBLOCK = "unblock"
    VIEW = "view"


class AuditLog(Base):
    """Modèle Log d'audit"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    
    action = Column(SQLEnum(AuditAction))
    entity_type = Column(String, nullable=False)  # user, transaction, etc.
    entity_id = Column(Integer, nullable=True)
    
    # Détails
    description = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    extra_metadata = Column(Text, nullable=True)  # JSON
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    admin = relationship("AdminUser")


class Operator(Base):
    """Modèle Opérateur Mobile Money"""
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Flooz, T-Money, Orange
    code = Column(String, unique=True, nullable=False)  # flooz, tmoney, orange
    api_endpoint = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Frais
    cash_in_fee_percent = Column(Float, default=1.0)
    cash_out_fee_percent = Column(Float, default=1.5)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class FraudAlert(Base):
    """Modèle Alerte de fraude"""
    __tablename__ = "fraud_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    
    # Détails
    risk_score = Column(Float, default=0.0)  # 0-100
    reason = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON
    
    # Statut
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relations
    user = relationship("User", foreign_keys=[user_id])
    transaction = relationship("Transaction")


class OfflineQueue(Base):
    """Modèle File d'attente offline"""
    __tablename__ = "offline_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Données de la transaction offline
    action_type = Column(String, nullable=False)  # send, cash_out, etc.
    payload = Column(Text, nullable=False)  # JSON
    
    # Statut de synchronisation
    is_synced = Column(Boolean, default=False)
    synced_at = Column(DateTime, nullable=True)
    sync_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    user = relationship("User")


class SystemSetting(Base):
    """Modèle Paramètres système"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String, nullable=True)
    
    # Type de valeur
    value_type = Column(String, default="string")  # string, number, boolean, json
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
