"""
Modèles Elna Market - Place de marché
Ajout des modèles Product, Order et OrderItem
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ProductCategory(str, enum.Enum):
    """Catégories de produits"""
    SERVICES = "services"
    PRODUITS = "produits"
    NUMERIQUES = "numeriques"
    AUTRE = "autre"


class OrderStatus(str, enum.Enum):
    """Statut des commandes"""
    EN_ATTENTE = "en_attente"
    PAYEE = "payee"
    EN_PREPARATION = "en_preparation"
    EXPEDIEE = "expediee"
    LIVREE = "livree"
    ANNULEE = "annulee"


class Product(Base):
    """Modèle Produit pour le marketplace"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(SQLEnum(ProductCategory), default=ProductCategory.AUTRE)
    image_url = Column(String, nullable=True)
    is_active = Column(Integer, default=True)
    stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    seller = relationship("User", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    """Modèle Commande pour le marketplace"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    seller_id = Column(Integer, ForeignKey("users.id"))
    
    # Détails commande
    total_amount = Column(Float, nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.EN_ATTENTE)
    shipping_address = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Paiement
    payment_status = Column(String, default="en_attente")
    payment_method = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller_user = relationship("User", foreign_keys=[seller_id])
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Modèle Article dans une commande"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
