"""
API Elna Market
Endpoints pour la place de marché
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User
from app.models.market import Product, Order, ProductCategory
from app.schemas.schemas import (
    ProductCreate, ProductResponse,
    OrderCreate, OrderResponse
)
from app.services.auth import get_current_active_user
from app.services.market.service import market_service

router = APIRouter(prefix="/market", tags=["🛒 Market"])


@router.get("/products", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = None,
    seller_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db)
):
    """Lister les produits"""
    products = market_service.get_products(db, category, seller_id, limit=limit)
    return products


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer un produit"""
    product = market_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Créer un produit"""
    # Activer le mode vendeur si pas encore fait
    if not current_user.is_seller:
        current_user.is_seller = True
        current_user.shop_name = current_user.username + "_shop"
        db.commit()
    
    return market_service.create_product(
        db=db,
        seller_id=current_user.id,
        name=product.name,
        description=product.description or "",
        price=product.price,
        category=product.category.value,
        stock=product.stock,
        image_url=product.image_url
    )


@router.get("/orders", response_model=List[OrderResponse])
def get_orders(
    as_buyer: bool = True,
    limit: int = Query(default=50, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Lister mes commandes"""
    return market_service.get_orders(db, current_user.id, as_buyer, limit)


@router.post("/orders", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Créer une commande"""
    try:
        items_data = [{"product_id": item.product_id, "quantity": item.quantity} for item in order.items]
        order_obj = market_service.create_order(
            db=db,
            buyer_id=current_user.id,
            seller_id=order.seller_id,
            items=items_data,
            shipping_address=order.shipping_address,
            notes=order.notes
        )
        return order_obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/pay")
def pay_order(
    order_id: int,
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Payer une commande via Elna Pay"""
    try:
        result = market_service.process_payment(
            db=db,
            order_id=order_id,
            buyer_id=current_user.id,
            account_id=account_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupérer une commande"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    # Vérifier que l'utilisateur est acheteur ou vendeur
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    return order


@router.get("/shop/stats")
def get_shop_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Statistiques de ma boutique"""
    if not current_user.is_seller:
        raise HTTPException(status_code=400, detail="Vous n'avez pas de boutique")
    
    return market_service.get_seller_stats(db, current_user.id)


@router.get("/sellers/{seller_id}/products")
def get_seller_products(
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Produits d'un vendeur"""
    products = market_service.get_products(db, seller_id=seller_id)
    return products
