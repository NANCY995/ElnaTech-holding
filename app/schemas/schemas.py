"""Schemas Pydantic pour la validation des données"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TransactionTypeEnum(str, Enum):
    ENCAISSEMENT = "encaissement"
    PAIEMENT = "paiement"
    TRANSFERT = "transfert"
    RETRAIT = "retrait"


class TransactionStatusEnum(str, Enum):
    EN_ATTENTE = "en_attente"
    VALIDEE = "validee"
    REJETEE = "rejetée"
    ANNULEE = "annulée"


# === Schemas Market ===
class ProductCategoryEnum(str, Enum):
    SERVICES = "services"
    PRODUITS = "produits"
    NUMERIQUES = "numeriques"
    AUTRE = "autre"


class OrderStatusEnum(str, Enum):
    EN_ATTENTE = "en_attente"
    PAYEE = "payee"
    EN_PREPARATION = "en_preparation"
    EXPEDIEE = "expediee"
    LIVREE = "livree"
    ANNULEE = "annulee"


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    category: ProductCategoryEnum = ProductCategoryEnum.AUTRE
    image_url: Optional[str] = None
    stock: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    seller_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, gt=0)


class OrderCreate(BaseModel):
    seller_id: int
    items: list[OrderItemCreate]
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    seller_id: int
    total_amount: float
    status: OrderStatusEnum
    shipping_address: Optional[str]
    notes: Optional[str]
    payment_status: str
    payment_method: Optional[str]
    created_at: datetime
    items: list[OrderItemResponse] = []
    
    class Config:
        from_attributes = True


# === Schemas Utilisateur ===
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# === Schemas Compte ===
class AccountBase(BaseModel):
    account_type: str = "professionnel"
    currency: str = "EUR"


class AccountCreate(AccountBase):
    pass


class AccountResponse(AccountBase):
    id: int
    user_id: int
    account_number: str
    balance: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# === Schemas Transaction ===
class TransactionBase(BaseModel):
    transaction_type: TransactionTypeEnum
    amount: float = Field(gt=0)
    description: Optional[str] = None
    recipient_account: Optional[str] = None
    recipient_name: Optional[str] = None
    category: Optional[str] = None


class TransactionCreate(TransactionBase):
    account_id: int


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    account_id: int
    currency: str
    status: TransactionStatusEnum
    fraud_score: float
    is_fraudulent: bool
    fraud_reason: Optional[str]
    created_at: datetime
    validated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TransactionWithFraud(TransactionResponse):
    """Transaction avec résultat de l'analyse de fraude"""
    fraud_analysis: Optional[dict] = None


# === Schemas Authentification ===
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# === Schemas Analyse Fraude ===
class FraudAnalysisResult(BaseModel):
    transaction_id: int
    fraud_score: float
    is_fraudulent: bool
    fraud_reason: Optional[str]
    risk_factors: list[str] = []
    recommendation: str
