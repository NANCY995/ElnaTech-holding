"""
Elna Credit 💰
Service de crédit et de scoring financier
Construit un dossier financier qui remplace les garanties bancaires
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Transaction, User


class CreditService:
    """
    Service de gestion du credit et du scoring financier
    """
    
    def calculate_credit_score(self, db: Session, user_id: int) -> dict:
        """
        Calcule le score de credit (0-1000)
        Ce score remplace les garanties bancaires traditionnelles
        """
        score = 500  # Score de base
        factors = []
        
        # Récupérer les données des 6 derniers mois
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= six_months_ago,
            Transaction.status == "validee"
        ).all()
        
        if not transactions:
            return {
                "score": 500,
                "grade": "C",
                "max_loan": 0,
                "factors": [{"name": "Aucune activité", "impact": 0, "description": "Commencez à utiliser Elna Pay pour construire votre dossier"}]
            }
        
        # 1. Volume d'activité (max 150 points)
        total_volume = sum(t.amount for t in transactions)
        if total_volume > 100000:
            score += 150
            factors.append({"name": "Volume d'activité", "impact": 150, "description": "Très forte activité (>100k€)"})
        elif total_volume > 50000:
            score += 100
            factors.append({"name": "Volume d'activité", "impact": 100, "description": "Forte activité (>50k€)"})
        elif total_volume > 20000:
            score += 50
            factors.append({"name": "Volume d'activité", "impact": 50, "description": "Activité modérée (>20k€)"})
        
        # 2. Régularité (max 100 points)
        months_active = len(set(t.created_at.strftime("%Y-%m") for t in transactions))
        if months_active >= 6:
            score += 100
            factors.append({"name": "Régularité", "impact": 100, "description": "Actif 6 mois consécutifs"})
        elif months_active >= 3:
            score += 50
            factors.append({"name": "Régularité", "impact": 50, "description": "Actif 3+ mois"})
        
        # 3. Ratio revenus/dépenses (max 150 points)
        encaissements = sum(t.amount for t in transactions if t.transaction_type == "encaissement")
        depenses = sum(t.amount for t in transactions if t.transaction_type != "encaissement")
        
        if encaissements > 0:
            ratio = encaissements / max(depenses, 1)
            if ratio >= 2.0:
                score += 150
                factors.append({"name": "Ratio financier", "impact": 150, "description": "Excellente santé financière (ratio >2)"})
            elif ratio >= 1.5:
                score += 100
                factors.append({"name": "Ratio financier", "impact": 100, "description": "Bonne santé financière (ratio >1.5)"})
            elif ratio >= 1.0:
                score += 50
                factors.append({"name": "Ratio financier", "impact": 50, "description": "Situation équilibrée"})
        
        # 4. Diversité des revenus (max 100 points)
        categories = set(t.category for t in transactions if t.transaction_type == "encaissement" and t.category)
        if len(categories) >= 3:
            score += 100
            factors.append({"name": "Diversité", "impact": 100, "description": f"{len(categories)} sources de revenus"})
        elif len(categories) >= 2:
            score += 50
            factors.append({"name": "Diversité", "impact": 50, "description": f"{len(categories)} sources de revenus"})
        
        # 5. Historique sans fraude (max 100 points)
        fraud_attempts = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_fraudulent == True
        ).count()
        
        if fraud_attempts == 0:
            score += 100
            factors.append({"name": "Sécurité", "impact": 100, "description": "Aucun incident de sécurité"})
        
        # 6. Fréquence des transactions (max 50 points)
        if len(transactions) >= 50:
            score += 50
            factors.append({"name": "Fréquence", "impact": 50, "description": "Très actif (50+ transactions)"})
        elif len(transactions) >= 20:
            score += 25
            factors.append({"name": "Fréquence", "impact": 25, "description": "Actif (20+ transactions)"})
        
        # Calculer le grade et le prêt max
        score = min(score, 1000)
        
        if score >= 800:
            grade = "A+"
            max_loan = min(total_volume * 0.5, 50000)
        elif score >= 700:
            grade = "A"
            max_loan = min(total_volume * 0.4, 30000)
        elif score >= 600:
            grade = "B"
            max_loan = min(total_volume * 0.3, 15000)
        elif score >= 500:
            grade = "C"
            max_loan = min(total_volume * 0.2, 5000)
        else:
            grade = "D"
            max_loan = 0
        
        return {
            "score": score,
            "grade": grade,
            "max_loan": round(max_loan, 2),
            "total_volume_6m": total_volume,
            "factors": factors
        }
    
    def get_loan_offers(self, db: Session, user_id: int) -> List[dict]:
        """
        Retourne les offres de prêt personnalisées basées sur le score
        """
        credit_profile = self.calculate_credit_score(db, user_id)
        
        offers = []
        
        # Offre de base
        offers.append({
            "name": "Elna Flash",
            "description": "Prêt rapide sans garantie",
            "amount": min(credit_profile["max_loan"], 5000),
            "rate": 0.08,  # 8% TAEG
            "duration_months": 12,
            "monthly_payment": round(min(credit_profile["max_loan"], 5000) / 12 * 1.08, 2),
            "required_score": 400
        })
        
        # Offre medium
        if credit_profile["score"] >= 500:
            offers.append({
                "name": "Elna Confort",
                "description": "Prêt personnalisé avec taux préférentiel",
                "amount": min(credit_profile["max_loan"], 15000),
                "rate": 0.06,  # 6% TAEG
                "duration_months": 24,
                "monthly_payment": round(min(credit_profile["max_loan"], 15000) / 24 * 1.06, 2),
                "required_score": 500
            })
        
        # Offre premium
        if credit_profile["score"] >= 700:
            offers.append({
                "name": "Elna Premium",
                "description": "Meilleur taux, montant élevé",
                "amount": min(credit_profile["max_loan"], 50000),
                "rate": 0.04,  # 4% TAEG
                "duration_months": 36,
                "monthly_payment": round(min(credit_profile["max_loan"], 50000) / 36 * 1.04, 2),
                "required_score": 700
            })
        
        return offers
    
    def simulate_loan(self, amount: float, months: int, rate: float) -> dict:
        """
        Simule un prêt et retourne les détails
        """
        # Calcul simple avec intérêts
        total = amount * (1 + rate)
        monthly = total / months
        
        return {
            "amount": amount,
            "rate": rate,
            "duration_months": months,
            "total_interest": round(total - amount, 2),
            "total_repayment": round(total, 2),
            "monthly_payment": round(monthly, 2)
        }
    
    def get_credit_report(self, db: Session, user_id: int) -> dict:
        """
        Génère un rapport de crédit complet
        """
        credit_profile = self.calculate_credit_score(db, user_id)
        offers = self.get_loan_offers(db, user_id)
        
        # Historique des 12 derniers mois
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        monthly_stats = []
        for i in range(12):
            month_date = datetime.utcnow() - timedelta(days=i*30)
            month_start = month_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            
            month_tx = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= month_start,
                Transaction.created_at < month_end,
                Transaction.status == "validee"
            ).all()
            
            enc = sum(t.amount for t in month_tx if t.transaction_type == "encaissement")
            dep = sum(t.amount for t in month_tx if t.transaction_type != "encaissement")
            
            monthly_stats.append({
                "month": month_start.strftime("%Y-%m"),
                "encaissements": enc,
                "depenses": dep,
                "net": enc - dep
            })
        
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "score": credit_profile["score"],
            "grade": credit_profile["grade"],
            "max_loan": credit_profile["max_loan"],
            "available_offers": offers,
            "monthly_history": list(reversed(monthly_stats))
        }


# Instance globale
credit_service = CreditService()
