"""
Elna Insights 📊
Service d'analyse et de business intelligence
Reçoit les données d'Elna Pay pour générer des insights métier
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Transaction, User


class InsightsService:
    """
    Service d'analyses avancées pour les données financières
    """
    
    def get_dashboard_summary(self, db: Session, user_id: int) -> dict:
        """Retourne le résumé du tableau de bord"""
        # Stats globales
        total_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).count()
        
        # Montants totaux
        encaissements = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "encaissement",
            Transaction.status == "validee"
        ).scalar() or 0
        
        depenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type.in_(["paiement", "transfert", "retrait"]),
            Transaction.status == "validee"
        ).scalar() or 0
        
        # Transactions ce mois
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= start_of_month
        ).count()
        
        return {
            "total_transactions": total_transactions,
            "total_encaisse": float(encaissements),
            "total_depenses": float(depenses),
            "balance": float(encaissements) - float(depenses),
            "month_transactions": month_transactions,
            "trend": self._calculate_trend(db, user_id)
        }
    
    def _calculate_trend(self, db: Session, user_id: int) -> str:
        """Calcule la tendance mois par mois"""
        now = datetime.utcnow()
        this_month = now.replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        
        this_month_tx = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= this_month,
            Transaction.status == "validee"
        ).count()
        
        last_month_tx = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= last_month,
            Transaction.created_at < this_month,
            Transaction.status == "validee"
        ).count()
        
        if this_month_tx > last_month_tx:
            return "up"
        elif this_month_tx < last_month_tx:
            return "down"
        return "stable"
    
    def get_revenue_by_category(self, db: Session, user_id: int, days: int = 30) -> List[dict]:
        """Retourne les revenus par catégorie"""
        since = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= since,
            Transaction.transaction_type == "encaissement",
            Transaction.status == "validee"
        ).group_by(Transaction.category).all()
        
        return [
            {
                "category": r.category or "non catégorisé",
                "total": float(r.total),
                "count": r.count,
                "percentage": 0  # Sera calculé côté client
            }
            for r in results
        ]
    
    def get_expenses_by_category(self, db: Session, user_id: int, days: int = 30) -> List[dict]:
        """Retourne les dépenses par catégorie"""
        since = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= since,
            Transaction.transaction_type.in_(["paiement", "transfert", "retrait"]),
            Transaction.status == "validee"
        ).group_by(Transaction.category).all()
        
        return [
            {
                "category": r.category or "non catégorisé",
                "total": float(r.total),
                "count": r.count
            }
            for r in results
        ]
    
    def get_daily_cashflow(self, db: Session, user_id: int, days: int = 30) -> List[dict]:
        """Retourne le flux de trésorerie quotidien"""
        since = datetime.utcnow() - timedelta(days=days)
        
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= since,
            Transaction.status == "validee"
        ).order_by(Transaction.created_at).all()
        
        # Grouper par jour
        daily_data = {}
        for tx in transactions:
            date_key = tx.created_at.strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {"date": date_key, "encaissements": 0, "depenses": 0}
            
            if tx.transaction_type == "encaissement":
                daily_data[date_key]["encaissements"] += tx.amount
            else:
                daily_data[date_key]["depenses"] += tx.amount
        
        return list(daily_data.values())
    
    def get_top_clients(self, db: Session, user_id: int, limit: int = 10) -> List[dict]:
        """Retourne les meilleurs clients (par encaissements)"""
        results = db.query(
            Transaction.recipient_name,
            Transaction.recipient_account,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "encaissement",
            Transaction.status == "validee",
            Transaction.recipient_name.isnot(None)
        ).group_by(
            Transaction.recipient_name,
            Transaction.recipient_account
        ).order_by(func.sum(Transaction.amount).desc()).limit(limit).all()
        
        return [
            {
                "name": r.recipient_name,
                "account": r.recipient_account,
                "total": float(r.total),
                "transactions": r.count
            }
            for r in results
        ]
    
    def get_top_suppliers(self, db: Session, user_id: int, limit: int = 10) -> List[dict]:
        """Retourne les principaux fournisseurs (par paiements)"""
        results = db.query(
            Transaction.recipient_name,
            Transaction.recipient_account,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "paiement",
            Transaction.status == "validee",
            Transaction.recipient_name.isnot(None)
        ).group_by(
            Transaction.recipient_name,
            Transaction.recipient_account
        ).order_by(func.sum(Transaction.amount).desc()).limit(limit).all()
        
        return [
            {
                "name": r.recipient_name,
                "account": r.recipient_account,
                "total": float(r.total),
                "transactions": r.count
            }
            for r in results
        ]
    
    def get_monthly_comparison(self, db: Session, user_id: int, months: int = 6) -> List[dict]:
        """Compare les revenus/dépenses sur plusieurs mois"""
        results = []
        
        for i in range(months):
            # Calculer le mois
            today = datetime.utcnow()
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_start = month_start.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            
            encaissements = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= month_start,
                Transaction.created_at < month_end,
                Transaction.transaction_type == "encaissement",
                Transaction.status == "validee"
            ).scalar() or 0
            
            depenses = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= month_start,
                Transaction.created_at < month_end,
                Transaction.transaction_type.in_(["paiement", "transfert", "retrait"]),
                Transaction.status == "validee"
            ).scalar() or 0
            
            results.append({
                "month": month_start.strftime("%Y-%m"),
                "month_name": month_start.strftime("%b"),
                "encaissements": float(encaissements),
                "depenses": float(depenses),
                "net": float(encaissements) - float(depenses)
            })
        
        return list(reversed(results))
    
    def get_fraud_statistics(self, db: Session, user_id: int) -> dict:
        """Statistiques sur les tentatives de fraude bloquées"""
        total_blocked = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_fraudulent == True,
            Transaction.status == "rejetée"
        ).count()
        
        high_risk = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.fraud_score >= 0.7
        ).count()
        
        avg_score = db.query(func.avg(Transaction.fraud_score)).filter(
            Transaction.user_id == user_id
        ).scalar() or 0
        
        return {
            "total_blocked": total_blocked,
            "high_risk_attempts": high_risk,
            "average_fraud_score": round(float(avg_score), 3),
            "protection_level": "Élevé" if total_blocked > 5 else "Moyen" if total_blocked > 0 else "Faible"
        }
    
    def get_business_health_score(self, db: Session, user_id: int) -> dict:
        """Calcule un score de santé financière"""
        # Récupérer les données des 30 derniers jours
        since = datetime.utcnow() - timedelta(days=30)
        
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= since,
            Transaction.status == "validee"
        ).all()
        
        if not transactions:
            return {"score": 0, "grade": "N/A", "factors": []}
        
        encaissements = sum(t.amount for t in transactions if t.transaction_type == "encaissement")
        depenses = sum(t.amount for t in transactions if t.transaction_type != "encaissement")
        
        factors = []
        score = 50  # Score de base
        
        # Ratio revenus/dépenses
        if depenses > 0:
            ratio = encaissements / depenses
            if ratio >= 1.5:
                score += 20
                factors.append({"name": "Ratio revenus/dépenses", "value": "Excellent", "points": 20})
            elif ratio >= 1.0:
                score += 10
                factors.append({"name": "Ratio revenus/dépenses", "value": "Bon", "points": 10})
            elif ratio < 0.5:
                score -= 15
                factors.append({"name": "Ratio revenus/dépenses", "value": "Attention", "points": -15})
        
        # Fréquence d'activité
        if len(transactions) >= 20:
            score += 15
            factors.append({"name": "Activité", "value": "Très active", "points": 15})
        elif len(transactions) >= 10:
            score += 10
            factors.append({"name": "Activité", "value": "Active", "points": 10})
        
        # Diversité des clients
        categories = set(t.category for t in transactions if t.category)
        if len(categories) >= 3:
            score += 15
            factors.append({"name": "Diversité", "value": "Variée", "points": 15})
        
        # Score final
        score = max(0, min(100, score))
        
        # Lettre
        if score >= 90:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 40:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": score,
            "grade": grade,
            "factors": factors,
            "recommendations": self._get_recommendations(score, factors)
        }
    
    def _get_recommendations(self, score: int, factors: list) -> List[str]:
        """Génère des recommandations personnalisées"""
        recommendations = []
        
        if score < 60:
            recommendations.append("Essayez d'augmenter vos revenus encaissés")
            recommendations.append("Diversifiez vos sources de revenus")
        
        if score < 75:
            recommendations.append("Maintenez une activité régulière")
            recommendations.append("Développez votre base de clients")
        
        if not any(f["name"] == "Diversité" for f in factors):
            recommendations.append("Diversifiez vos catégories de revenus")
        
        if not recommendations:
            recommendations.append("Excellent ! Continuez comme ça")
        
        return recommendations


# Instance globale
insights_service = InsightsService()
