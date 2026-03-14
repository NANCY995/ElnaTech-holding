"""
Elna Comply 📋
Service de conformité fiscale automatique
Génère les déclarations fiscales à partir des données Elna Pay
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Transaction, User


class ComplyService:
    """
    Service de déclarations fiscales automatiques
    """
    
    def get_tax_summary(self, db: Session, user_id: int, year: int = None) -> dict:
        """
        Calcule le résumé fiscal pour une année
        """
        if year is None:
            year = datetime.utcnow().year
        
        # Période fiscale
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        # Récupérer toutes les transactions validées
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == "validee"
        ).all()
        
        # Calculer les revenus par catégorie
        revenus = {}
        depenses = {}
        
        for tx in transactions:
            cat = tx.category or "autre"
            
            if tx.transaction_type == "encaissement":
                revenus[cat] = revenus.get(cat, 0) + tx.amount
            else:
                depenses[cat] = depenses.get(cat, 0) + tx.amount
        
        # Calculs globaux
        total_revenus = sum(revenus.values())
        total_depenses = sum(depenses.values())
        benefice = total_revenus - total_depenses
        
        # Estimer l'impôt (simplifié)
        # Pour micro-BNC ou freelance
        if benefice > 0:
            # Abattement forfaitaire de 10%
            revenu_imposable = benefice * 0.9
            
            if revenu_imposable < 10777:
                impôt = 0
            elif revenu_imposable < 27478:
                impôt = (revenu_imposable - 10777) * 0.11
            elif revenu_imposable < 78570:
                impôt = (revenu_imposable - 27478) * 0.30 + 1847
            else:
                impôt = (revenu_imposable - 78570) * 0.41 + 18175
        else:
            impôt = 0
        
        return {
            "year": year,
            "periode": f"01/01/{year} - 31/12/{year}",
            "total_revenus": round(total_revenus, 2),
            "total_depenses": round(total_depenses, 2),
            "benefice": round(benefice, 2),
            "revenu_imposable": round(benefice * 0.9, 2),
            "impot_estime": round(impôt, 2),
            "revenus_par_categorie": revenus,
            "depenses_par_categorie": depenses,
            "nombre_transactions": len(transactions)
        }
    
    def generate_declaration(self, db: Session, user_id: int, year: int = None) -> dict:
        """
        Génère une déclaration de revenus prête à soumettre
        """
        if year is None:
            year = datetime.utcnow().year - 1  # Année N-1 pour déclaration
        
        tax_summary = self.get_tax_summary(db, user_id, year)
        
        # Générer les lignes de déclaration
        declaration = {
            "Informations générales": {
                "Année": year,
                "Date générée": datetime.utcnow().isoformat(),
                "Type de revenus": "BNC (Bénéfices Non Commerciaux)"
            },
            "Chiffre d'affaires": {
                "Total des encaissements": tax_summary["total_revenus"],
                "Nombre de transactions": tax_summary["nombre_transactions"]
            },
            "Charges déductibles": {
                "Total des dépenses": tax_summary["total_depenses"]
            },
            "Résultat": {
                "Bénéfice brut": tax_summary["benefice"],
                "Abattement forfaitaire (10%)": round(tax_summary["benefice"] * 0.1, 2),
                "Revenu imposable": tax_summary["revenu_imposable"]
            },
            "Impôt estimé": {
                "Montant": tax_summary["impot_estime"],
                "Note": "Estimation basée sur le barème simplification"
            }
        }
        
        return declaration
    
    def get_tva_summary(self, db: Session, user_id: int, year: int = None, quarter: int = None) -> dict:
        """
        Calcule le résumé TVA (simplifié)
        """
        if year is None:
            year = datetime.utcnow().year
        
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        # Transactions avec TVA (fictif pour l'exemple - 20%)
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == "validee",
            Transaction.transaction_type.in_(["paiement", "retrait"])
        ).all()
        
        # Calcul TVA (simplifié)
        total_ht = sum(t.amount for t in transactions) / 1.20
        tva_collectee = sum(t.amount for t in transactions) - total_ht
        
        return {
            "year": year,
            "quarter": quarter,
            "total_ht": round(total_ht, 2),
            "tva_collectee": round(tva_collectee, 2),
            "tva_deductible": 0,  # Simplifié
            "tva_due": round(tva_collectee, 2)
        }
    
    def get_social_contributions(self, db: Session, user_id: int, year: int = None) -> dict:
        """
        Calcule les cotisations sociales estimées
        """
        if year is None:
            year = datetime.utcnow().year
        
        tax_summary = self.get_tax_summary(db, user_id, year)
        benefice = tax_summary["benefice"]
        
        # Estimation charges sociales (simplifié)
        # Micro-BNC : environ 22% du revenu
        if benefice > 0:
            cotisations = benefice * 0.22
        else:
            cotisations = 0
        
        return {
            "year": year,
            "benefice": benefice,
            "cotisations_sociales_estimees": round(cotisations, 2),
            "taux": "22% (estimation micro-BNC)",
            "note": "Contribuable responsable du montant réel"
        }
    
    def get_annual_report(self, db: Session, user_id: int, year: int = None) -> dict:
        """
        Génère un rapport annuel complet
        """
        if year is None:
            year = datetime.utcnow().year - 1
        
        tax = self.get_tax_summary(db, user_id, year)
        tva = self.get_tva_summary(db, user_id, year)
        social = self.get_social_contributions(db, user_id, year)
        
        return {
            "rapport_annuel": {
                "annee": year,
                "genere_le": datetime.utcnow().isoformat()
            },
            "fiscal": tax,
            "tva": tva,
            "social": social,
            "total_impots_et_cotisations": round(
                tax["impot_estime"] + social["cotisations_sociales_estimees"], 2
            )
        }


# Instance globale
comply_service = ComplyService()
