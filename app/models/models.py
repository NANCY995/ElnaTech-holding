"""Modèles de base de données pour Elna Pay"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TransactionType(str, enum.Enum):
    """Types de transactions"""
    ENCAISSEMENT = "encaissement"      # Recevoir de l'argent
    PAIEMENT = "paiement"              # Payer un fournisseur
    TRANSFERT = "transfert"            # Transfert vers autre compte
    RETRAIT = "retrait"                # Retrait espèces


class TransactionStatus(str, enum.Enum):
    """Statut des transactions"""
    EN_ATTENTE = "en_attente"
    VALIDEE = "validee"
    REJETEE = "rejetée"
    ANNULEE = "annulée"


class User(Base):
    """Modèle Utilisateur"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Integer, default=True)
    is_seller = Column(Integer, default=False)  # Peut vendre sur le market
    shop_name = Column(String, nullable=True)  # Nom de la boutique
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    accounts = relationship("Account", back_populates="owner")
    transactions = relationship("Transaction", back_populates="user")
    products = relationship("Product", back_populates="seller")
    orders = relationship("Order", back_populates="buyer", foreign_keys="Order.buyer_id")
    shop_orders = relationship("Order", back_populates="seller_user", foreign_keys="Order.seller_id")


class Account(Base):
    """Modèle Compte bancaire"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_number = Column(String, unique=True, index=True)
    account_type = Column(String)  # "professionnel", "entreprise"
    balance = Column(Float, default=0.0)
    currency = Column(String, default="EUR")
    is_active = Column(Integer, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    owner = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    """Modèle Transaction"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    
    # Détails transaction
    transaction_type = Column(SQLEnum(TransactionType))
    amount = Column(Float)
    currency = Column(String, default="EUR")
    description = Column(String, nullable=True)
    
    # Statut et sécurité
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.EN_ATTENTE)
    fraud_score = Column(Float, default=0.0)  # Score de fraude IA
    is_fraudulent = Column(Integer, default=False)
    fraud_reason = Column(String, nullable=True)
    
    # Metadata
    recipient_account = Column(String, nullable=True)
    recipient_name = Column(String, nullable=True)
    category = Column(String, nullable=True)  # Catégorie (fournisseur, client, etc.)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)
    
    # Relations
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")


class TransactionHistory(Base):
    """Historique des transactions pour analyse IA"""
    __tablename__ = "transaction_history"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Patterns détectés
    amount_normalized = Column(Float)  # Montant normalisé
    time_hour = Column(Integer)
    day_of_week = Column(Integer)
    is_recurring = Column(Integer, default=False)
    merchant_category = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
