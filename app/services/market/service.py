"""
Elna Market 🛒
Service de place de marché intégrée
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.market import Product, Order, OrderItem, ProductCategory, OrderStatus
from app.models.models import Account, Transaction, TransactionType, TransactionStatus, User


class MarketService:
    """
    Service de gestion de la place de marché
    """
    
    def create_product(
        self, 
        db: Session, 
        seller_id: int, 
        name: str,
        description: str,
        price: float,
        category: str = "autre",
        stock: int = 0,
        image_url: str = None
    ) -> Product:
        """Créer un nouveau produit"""
        product = Product(
            seller_id=seller_id,
            name=name,
            description=description,
            price=price,
            category=ProductCategory(category),
            stock=stock,
            image_url=image_url
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    
    def get_products(
        self, 
        db: Session, 
        category: str = None,
        seller_id: int = None,
        active_only: bool = True,
        limit: int = 50
    ) -> List[Product]:
        """Lister les produits"""
        query = db.query(Product)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        if category:
            query = query.filter(Product.category == ProductCategory(category))
        
        if seller_id:
            query = query.filter(Product.seller_id == seller_id)
        
        return query.order_by(Product.created_at.desc()).limit(limit).all()
    
    def get_product(self, db: Session, product_id: int) -> Optional[Product]:
        """Récupérer un produit"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    def create_order(
        self,
        db: Session,
        buyer_id: int,
        seller_id: int,
        items: list,
        shipping_address: str = None,
        notes: str = None
    ) -> Order:
        """Créer une commande"""
        # Calculer le total
        total = 0
        order_items = []
        
        for item in items:
            product = self.get_product(db, item["product_id"])
            if not product:
                raise ValueError(f"Produit {item['product_id']} non trouvé")
            
            if product.stock < item.get("quantity", 1):
                raise ValueError(f"Stock insuffisant pour {product.name}")
            
            quantity = item.get("quantity", 1)
            subtotal = product.price * quantity
            total += subtotal
            
            order_items.append({
                "product": product,
                "quantity": quantity,
                "unit_price": product.price,
                "subtotal": subtotal
            })
        
        # Créer la commande
        order = Order(
            buyer_id=buyer_id,
            seller_id=seller_id,
            total_amount=total,
            shipping_address=shipping_address,
            notes=notes,
            status=OrderStatus.EN_ATTENTE,
            payment_status="en_attente"
        )
        db.add(order)
        db.flush()  # Pour obtenir l'ID
        
        # Créer les items
        for item in order_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product"].id,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                subtotal=item["subtotal"]
            )
            db.add(order_item)
            
            # Réduire le stock
            item["product"].stock -= item["quantity"]
        
        db.commit()
        db.refresh(order)
        return order
    
    def process_payment(
        self,
        db: Session,
        order_id: int,
        buyer_id: int,
        account_id: int
    ) -> dict:
        """Traiter le paiement d'une commande via Elna Pay"""
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise ValueError("Commande non trouvée")
        
        if order.buyer_id != buyer_id:
            raise ValueError("Cette commande ne vous appartient pas")
        
        if order.payment_status == "payee":
            raise ValueError("Commande déjà payée")
        
        # Vérifier le solde
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == buyer_id
        ).first()
        
        if not account:
            raise ValueError("Compte non trouvé")
        
        if account.balance < order.total_amount:
            raise ValueError("Solde insuffisant")
        
        # Créer la transaction de paiement
        transaction = Transaction(
            user_id=buyer_id,
            account_id=account_id,
            transaction_type=TransactionType.PAIEMENT,
            amount=order.total_amount,
            description=f"Paiement commande #{order.id}",
            status=TransactionStatus.VALIDEE
        )
        
        # Débiter l'acheteur
        account.balance -= order.total_amount
        
        # Mettre à jour le statut de la commande
        order.payment_status = "payee"
        order.status = OrderStatus.PAYEE
        
        db.add(transaction)
        db.commit()
        db.refresh(order)
        
        return {
            "order_id": order.id,
            "amount": order.total_amount,
            "status": "payee",
            "transaction_id": transaction.id
        }
    
    def get_orders(
        self,
        db: Session,
        user_id: int,
        as_buyer: bool = True,
        limit: int = 50
    ) -> List[Order]:
        """Lister les commandes"""
        if as_buyer:
            return db.query(Order).filter(
                Order.buyer_id == user_id
            ).order_by(Order.created_at.desc()).limit(limit).all()
        else:
            return db.query(Order).filter(
                Order.seller_id == user_id
            ).order_by(Order.created_at.desc()).limit(limit).all()
    
    def update_order_status(
        self,
        db: Session,
        order_id: int,
        seller_id: int,
        new_status: str
    ) -> Order:
        """Mettre à jour le statut d'une commande (par le vendeur)"""
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise ValueError("Commande non trouvée")
        
        if order.seller_id != seller_id:
            raise ValueError("Vous n'êtes pas le vendeur de cette commande")
        
        order.status = OrderStatus(new_status)
        db.commit()
        db.refresh(order)
        return order
    
    def get_seller_stats(self, db: Session, seller_id: int) -> dict:
        """Statistiques du vendeur"""
        orders = db.query(Order).filter(
            Order.seller_id == seller_id,
            Order.payment_status == "payee"
        ).all()
        
        products = db.query(Product).filter(Product.seller_id == seller_id).all()
        
        total_sales = sum(o.total_amount for o in orders)
        
        return {
            "total_orders": len(orders),
            "total_sales": total_sales,
            "active_products": len([p for p in products if p.is_active]),
            "pending_orders": len([o for o in orders if o.status == OrderStatus.PAYEE])
        }


# Instance globale
market_service = MarketService()
