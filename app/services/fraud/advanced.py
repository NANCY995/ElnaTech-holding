"""
Service IA de Détection de Fraude - Amélioré
Phase 5 - Règles avancées et scoring de risque
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.models import Transaction, User


class FraudDetectionService:
    """
    Service de détection de fraude avec IA
    Combine règles basiques et scoring probabiliste
    """
    
    # Seuils de configuration
    THRESHOLD_HIGH = 75  # Bloquer
    THRESHOLD_MEDIUM = 50  # Confirmer
    THRESHOLD_LOW = 25  # Avertir
    
    # Limites par défaut
    DAILY_LIMIT_DEFAULT = 50000
    TRANSACTION_LIMIT_DEFAULT = 10000
    
    def __init__(self):
        self.rules = [
            self.rule_amount_too_high,
            self.rule_unusual_frequency,
            self.rule_new_beneficiary,
            self.rule_night_transaction,
            self.rule_geo_anomaly,
            self.rule_first_large_transaction,
            self.rule_rapid_succession,
            self.rule_unusual_category,
        ]
    
    def analyze_transaction(
        self,
        db: Session,
        user_id: int,
        amount: float,
        transaction_type: str = "paiement",
        recipient_id: int = None,
        category: str = None
    ) -> Dict:
        """
        Analyse une transaction et retourne le score de risque
        """
        # Récupérer l'historique utilisateur
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.status == "validee"
        ).order_by(Transaction.created_at.desc()).limit(30).all()
        
        # Calculer le score
        risk_score = 0
        triggered_rules = []
        
        for rule in self.rules:
            result = rule(db, user_id, amount, transaction_type, recipient_id, category, transactions)
            if result["triggered"]:
                risk_score += result["score"]
                triggered_rules.append(result)
        
        # Déterminer le niveau de risque
        if risk_score >= self.THRESHOLD_HIGH:
            level = "HIGH"
            action = "BLOCK"
            message = "Transaction bloquée - risque élevé détecté"
        elif risk_score >= self.THRESHOLD_MEDIUM:
            level = "MEDIUM"
            action = "REVIEW"
            message = "Transaction en attente de confirmation"
        elif risk_score >= self.THRESHOLD_LOW:
            level = "LOW"
            action = "ALERT"
            message = "Alerte enregistrée - transaction traitée"
        else:
            level = "MINIMAL"
            action = "APPROVE"
            message = "Transaction approuvée"
        
        return {
            "risk_score": min(risk_score, 100),
            "level": level,
            "action": action,
            "message": message,
            "triggered_rules": triggered_rules,
            "should_block": risk_score >= self.THRESHOLD_HIGH
        }
    
    # === Règles de détection ===
    
    def rule_amount_too_high(
        self, db, user_id, amount, tx_type, recipient_id, category, transactions
    ) -> Dict:
        """Transaction > 3x la moyenne des 30 derniers jours"""
        if not transactions:
            return {"triggered": False, "score": 0, "rule": "amount_too_high", "reason": ""}
        
        avg_amount = sum(t.amount for t in transactions) / len(transactions)
        
        if amount > avg_amount * 3 and amount > 1000:
            return {
                "triggered": True,
                "score": 30,
                "rule": "amount_too_high",
                "reason": f"Montant {amount}€ > 3x moyenne ({avg_amount:.0f}€)"
            }
        return {"triggered": False, "score": 0, "rule": "amount_too_high", "reason": ""}
    
    def rule_unusual_frequency(
        self, db, user_id, amount, tx_type, recipient_id, category, transactions
    ) -> Dict:
        """Plus de 10 transactions en moins de 5 minutes"""
        if len(transactions) < 10:
            return {"triggered": False, "score": 0, "rule": "unusual_frequency", "reason": ""}
        
        recent = [t for t in transactions if t.created_at > datetime.utcnow() - timedelta(minutes=5)]
        
        if len(recent) > 10:
            return {
                "triggered": True,
                "score": 35,
                "rule": "unusual_frequency",
                "reason": f"{len(recent)} transactions en 5 minutes"
            }
        return {"triggered": False, "score": 0, "rule": "unusual_frequency", "reason": ""}
    
    def rule_new_beneficiary(
        self, db, user_id, amount, tx_type, recipient_id, category, transactions
    ) -> Dict:
        """Nouveau bénéficiaire + montant élevé"""
        if not recipient_id or amount < 500:
            return {"triggered": False, "score": 0, "rule": "new_beneficiary", "reason": ""}
        
        existing_recipients = set()
        for t in transactions[:20]:
            if t.recipient_id:
                existing_recipients.add(t.recipient_id)
        
        if recipient_id not in existing_recipients:
            return {
                "triggered": True,
                "score": 25,
                "rule": "new_beneficiary",
                "reason": f"Nouveau bénéficiaire avec montant {amount}€"
            }
        return {"triggered": False, "score": 0, "rule": "new_beneficiary", "reason": ""}
    
    def rule_night_transaction(
        self, db, user_id, amount, tx_type, recipient_id, category, transactions
    ) -> Dict:
        """Transaction entre 23h et 5h"""
        current_hour = datetime.utcnow().hour
        
        if current_hour >= 23 or current_hour < 5:
            if amount > 500:
                return {
                    "triggered": True,
                    "score": 20,
                    "rule": "night_transaction",
                    "reason": f"Transaction nocturne de {amount}€"
                }
        return {"triggered": False, "score": 0, "rule": "night_transaction", "reason": ""}
    
    def rule_geo_anomaly(
        self, db, user_id, amount, tx_type, recipient_id, category, transactions
    ) -> Dict:
        """Anomalie géographique (simplifié)"""
        return {"triggered": False, "score": 0, "rule": "geo_anomaly", "reason": ""}
    
    def rule_first_large_transaction(
        self, db, user_id, amount, tx_type, recipient_id, category, transactions
    ) -> Dict:
        """Première transaction importante pour un nouveau compte"""
        if transactions or amount < 1000:
            return {"triggered": False, "score": 0, "rule": "first_large_transaction", "reason": ""}
        
        return {
            "triggered": True,
            "score": 15,
            "rule": "first_large_transaction",
            "reason": f"Première transaction importante: {amount}€"
        }
    
    def rule_rapid_succession(
        self, db, user_id, amount, tx_type, recipient_id, category, transactions
    ) -> Dict:
        """Transactions successives rapides vers le même bénéficiaire"""
        if not recipient_id or len(transactions) < 2:
            return {"triggered": False, "score": 0, "rule": "rapid_succession", "reason": ""}
        
        recent_same = [
            t for t in transactions[:5]
            if t.recipient_id == recipient_id
            and t.created_at > datetime.utcnow() - timedelta(minutes=10)
        ]
        
        if len(recent_same) >= 2:
            return {
                "triggered": True,
                "score": 25,
                "rule": "rapid_succession",
                "reason": f"{len(recent_same)} transactions en 10 min vers même bénéficiaire"
            }
        return {"triggered": False, "score": 0, "rule": "rapid_succession", "reason": ""}
    
    def rule_unusual_category(
        self, db, user_id, amount, tx_type, recipient_id, category, transactions
    ) -> Dict:
        """Catégorie inhabituelle pour l'utilisateur"""
        if not category:
            return {"triggered": False, "score": 0, "rule": "unusual_category", "reason": ""}
        
        categories = {}
        for t in transactions:
            cat = t.category or "autre"
            categories[cat] = categories.get(cat, 0) + 1
        
        if categories and category not in categories:
            return {
                "triggered": True,
                "score": 10,
                "rule": "unusual_category",
                "reason": f"Catégorie inhabituelle: {category}"
            }
        return {"triggered": False, "score": 0, "rule": "unusual_category", "reason": ""}
    
    def get_user_risk_profile(self, db: Session, user_id: int) -> Dict:
        """Profil de risque global de l'utilisateur"""
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).all()
        
        if not transactions:
            return {
                "user_id": user_id,
                "risk_level": "UNKNOWN",
                "total_transactions": 0,
                "total_volume": 0,
                "average_amount": 0,
                "flags": []
            }
        
        amounts = [t.amount for t in transactions]
        total = sum(amounts)
        avg = total / len(amounts)
        
        flags = []
        if len(transactions) > 100:
            flags.append("high_volume")
        if max(amounts) > avg * 5:
            flags.append("high_variance")
        
        risk_score = min(100, len(transactions) * 2 + len(flags) * 10)
        
        return {
            "user_id": user_id,
            "risk_level": "HIGH" if risk_score > 70 else "MEDIUM" if risk_score > 40 else "LOW",
            "total_transactions": len(transactions),
            "total_volume": round(total, 2),
            "average_amount": round(avg, 2),
            "max_transaction": max(amounts),
            "risk_score": risk_score,
            "flags": flags
        }


# Instance globale
fraud_service = FraudDetectionService()
