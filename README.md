# Elna Pay - Plateforme de Paiement Mobile UEMOA

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.12+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-orange)

## À propos

Elna Pay est une plateforme de paiement mobile conçue pour le marché UEMOA (Union Économique et Monétaire Ouest-Africaine).

## Fonctionnalités

### 💳 Elna Pay - Paiements
- Inscription/connexion utilisateur avec JWT
- Création automatique de compte IBAN
- Transactions : encaissements, paiements, transferts, retraits
- 🤖 IA de détection de fraude en temps réel

### 📊 Elna Insights - Analytics
- Dashboard avec statistiques complètes
- Revenus/dépenses par catégorie

### 💰 Elna Credit - Score Financier
- Score de crédit (0-1000)
- Offres de prêt personnalisées

### 📋 Elna Comply - Fiscalité
- Résumé fiscal annuel
- Déclaration de revenus automatique

### 🛒 Elna Market - Place de Marché
- Gestion des produits et commandes

### 🪪 KYC - Vérification d'Identité
- Vérification de document
- Selfie avec liveness check

## Installation

```bash
# Installer les dépendances
uv pip install -r requirements.txt

# Lancer le serveur
uv run uvicorn app.main:app --reload
```

## Docker

```bash
# Développement
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tests

```bash
pytest tests/ -v
```

## Licence

Propriétaire - Elna Tech Holding
