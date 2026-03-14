"""
Service d'IA de détection de fraude 🔒
Analyse chaque transaction en temps réel pour détecter les anomalies et tentatives de fraude
"""
import random
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import Transaction, User, TransactionHistory
from app.core.config import get_settings

settings = get_settings()


class FraudDetectionService:
    """
    Service d'IA pour la détection de fraude
    Analyse les transactions en temps réel
    """
    
    def __init__(self):
        self.threshold = settings.ANOMALY_THRESHOLD
        self.enabled = settings.FRAUD_DETECTION_ENABLED
        
    def analyze_transaction(
        self, 
        db: Session, 
        transaction: Transaction,
        user: User
    ) -> dict:
        """
        Analyse une transaction pour détecter une fraude potentielle
        
        Returns:
            dict avec fraud_score, is_fraudulent, fraud_reason, risk_factors
        """
        if not self.enabled:
            return {
                "fraud_score": 0.0,
                "is_fraudulent": False,
                "fraud_reason": None,
                "risk_factors": [],
                "recommendation": "approve"
            }
        
        risk_factors = []
        fraud_score = 0.0
        
        # 1. Analyser le montant
        amount_analysis = self._analyze_amount(db, transaction, user)
        fraud_score += amount_analysis["score"]
        risk_factors.extend(amount_analysis["factors"])
        
        # 2. Analyser le comportement temporel
        time_analysis = self._analyze_time_pattern(transaction, user)
        fraud_score += time_analysis["score"]
        risk_factors.extend(time_analysis["factors"])
        
        # 3. Analyser la fréquence
        frequency_analysis = self._analyze_frequency(db, transaction, user)
        fraud_score += frequency_analysis["score"]
        risk_factors.extend(frequency_analysis["factors"])
        
        # 4. Analyser le destinataire
        recipient_analysis = self._analyze_recipient(transaction)
        fraud_score += recipient_analysis["score"]
        risk_factors.extend(recipient_analysis["factors"])
        
        # Normaliser le score entre 0 et 1
        fraud_score = min(fraud_score / 4.0, 1.0)
        
        # Déterminer si c'est frauduleux
        is_fraudulent = fraud_score >= self.threshold
        
        # Générer une raison
        fraud_reason = None
        if is_fraudulent:
            fraud_reason = self._generate_fraud_reason(risk_factors)
        
        # Recommandation
        recommendation = "reject" if is_fraudulent else "approve"
        if fraud_score >= 0.5:
            recommendation = "review"
            
        return {
            "fraud_score": round(fraud_score, 3),
            "is_fraudulent": is_fraudulent,
            "fraud_reason": fraud_reason,
            "risk_factors": risk_factors[:5],  # Limiter à 5 facteurs
            "recommendation": recommendation
        }
    
    def _analyze_amount(self, db: Session, transaction: Transaction, user: User) -> dict:
        """Analyse du montant de la transaction"""
        factors = []
        score = 0.0
        
        # Récupérer l'historique des montants pour cet utilisateur
        history = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.status == "validee"
        ).all()
        
        if history:
            avg_amount = sum(t.amount for t in history) / len(history)
            max_amount = max(t.amount for t in history)
            
            # Montant inhabituel (> 3x la moyenne)
            if transaction.amount > avg_amount * 3:
                factors.append(f"Montant 3x supérieur à la moyenne ({avg_amount:.2f}€)")
                score += 0.3
            
            # Montant record
            if transaction.amount > max_amount * 1.5:
                factors.append("Nouveau montant record")
                score += 0.25
        else:
            # Première transaction - vigilance accrue
            factors.append("Première transaction détectée")
            score += 0.15
        
        # Montant suspect (> 10000€)
        if transaction.amount > 10000:
            factors.append("Montant élevé (> 10000€)")
            score += 0.2
            
        return {"score": score, "factors": factors}
    
    def _analyze_time_pattern(self, transaction: Transaction, user: User) -> dict:
        """Analyse des patterns temporels"""
        factors = []
        score = 0.0
        
        hour = transaction.created_at.hour
        day = transaction.created_at.weekday()
        
        # Transaction pendant les heures inhabituelles (nuit)
        if hour >= 0 and hour <= 5:
            factors.append("Transaction pendant les heures nocturnes")
            score += 0.2
        
        # Transaction le weekend
        if day >= 5:  # Samedi ou Dimanche
            factors.append("Transaction le weekend")
            score += 0.1
            
        return {"score": score, "factors": factors}
    
    def _analyze_frequency(self, db: Session, transaction: Transaction, user: User) -> dict:
        """Analyse de la fréquence des transactions"""
        factors = []
        score = 0.0
        
        # Compter les transactions des dernières 24h
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_count = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.created_at >= yesterday
        ).count()
        
        if recent_count > 10:
            factors.append(f"Nombreux transactions en 24h ({recent_count})")
            score += 0.25
            
        return {"score": score, "factors": factors}
    
    def _analyze_recipient(self, transaction: Transaction) -> dict:
        """Analyse du destinataire"""
        factors = []
        score = 0.0
        
        # Nouveau destinataire pour un transfert
        if transaction.transaction_type in ["transfert", "paiement"]:
            if not transaction.recipient_account:
                factors.append("Destinataire non vérifié")
                score += 0.15
        
        return {"score": score, "factors": factors}
    
    def _generate_fraud_reason(self, risk_factors: list) -> str:
        """Génère une raison de fraude basée sur les facteurs de risque"""
        if not risk_factors:
            return "Activité suspecte détectée par l'IA"
        
        # Retourner le facteur de risque le plus significatif
        return risk_factors[0]
    
    def learn_from_feedback(
        self, 
        transaction_id: int, 
        db: Session,
        is_legitimate: bool
    ):
        """
        Apprend du feedback (pour améliorer le modèle)
        Cette méthode pourrait être étendue pour entraîner un vrai modèle ML
        """
        # Dans une vraie implémentation, cela permettrait d'affiner le modèle
        # Pour l'instant, c'est un placeholder
        pass


# Instance globale du service
fraud_service = FraudDetectionService()
