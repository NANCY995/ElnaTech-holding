# Elna Tech Holding - Spécifications Techniques

## Vision

Elna Tech Holding est un écosystème de services financiers intégrés pour l'Afrique de l'Ouest (UEMOA), propulsé par l'IA.

## Architecture

```
Elna Tech Holding
│
├── Elna Pay 💳 (Backend API)
│   ├── FastAPI + SQLAlchemy + SQLite/PostgreSQL
│   ├── Auth JWT
│   ├── Transactions (encaissement, paiement, retrait, transfert)
│   ├── IBAN virtuels
│   ├── IA Détection de fraude (8 règles)
│   ├── KYC intégré
│   └── Mobile Money (Flooz, T-Money, Orange, Moov)
│
├── Elna Insights 📊
│   ├── KPIs financiers
│   ├── Analyse des tendances
│   ├── Segmentation clients
│   └── Rapports fraude
│
├── Elna Credit 💰
│   ├── Score de crédit (0-1000)
│   ├── Offres de prêt personnalisées
│   └── Simulateur de prêt
│
├── Elna Comply 📋
│   ├── Déclarations fiscales automatiques
│   ├── Suivi des échéances
│   └── Résumé fiscal annuel
│
└── Elna Market 🏪
    ├── Gestion produits
    ├── Commandes
    ├── Panier
    └── Paiements intégrés
```

## Stack Technique

- **Backend**: Python 3.12 + FastAPI
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ORM**: SQLAlchemy 2.0
- **Auth**: JWT (python-jose)
- **Frontend**: HTML/CSS/JS (static files)
- **Cache**: Redis (production)
- **Container**: Docker + Docker Compose

## Modèles de Données

### User
- id, email, username, hashed_password
- full_name, phone, is_active, is_seller
- shop_name, kyc_level, credit_score

### Account
- id, user_id, account_number (IBAN)
- balance, currency, is_active

### Transaction
- id, user_id, account_id
- amount, transaction_type (encaissement/paiement/retrait/transfert)
- status (en_attente/validee/rejetee)
- category, description, recipient_id

### FraudAlert
- id, user_id, risk_score, reason
- is_resolved, resolved_by, resolved_at

### KYCRecord
- id, user_id, document_type, document_number
- status (non_initie/en_cours/en_attente/verifie/rejete)
- verified_at

### Product (Market)
- id, seller_id, name, description, price
- category, stock, images

### Order (Market)
- id, buyer_id, seller_id, total_amount
- status, payment_status

## API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/refresh
- GET /api/auth/me

### Transactions
- POST /api/transactions
- GET /api/transactions
- GET /api/transactions/{id}
- GET /api/transactions/history

### Mobile Money
- GET /api/mobile-money/operators
- POST /api/mobile-money/cash-in
- POST /api/mobile-money/cash-out
- GET /api/mobile-money/fees/{operator}

### KYC
- POST /api/kyc/initiate
- POST /api/kyc/document
- POST /api/kyc/selfie
- GET /api/kyc/status

### Insights
- GET /api/insights/summary
- GET /api/insights/categories
- GET /api/insights/trends
- GET /api/insights/fraud-report

### Credit
- GET /api/credit/score
- GET /api/credit/offers
- POST /api/credit/simulator

### Comply
- GET /api/comply/tax-summary
- GET /api/comply/deadlines
- GET /api/comply/annual-report

### Market
- GET /api/market/products
- POST /api/market/products
- POST /api/market/orders
- GET /api/market/orders

### Admin
- GET /api/admin/dashboard/stats
- GET /api/admin/users
- POST /api/admin/users/{id}/suspend
- GET /api/admin/transactions
- GET /api/admin/fraud-alerts

## IA - Détection de Fraude

Règles implémentées (score total 0-100):
1. **Montant trop élevé** (>3x moyenne) - 30 points
2. **Fréquence inhabituelle** (>10 tx/5min) - 35 points
3. **Nouveau bénéficiaire** + montant élevé - 25 points
4. **Transaction nocturne** (23h-5h) - 20 points
5. **Première transaction importante** - 15 points
6. **Succession rapide** (même bénéficiaire) - 25 points
7. **Catégorie inhabituelle** - 10 points

Seuils:
- >= 75: BLOCK
- >= 50: REVIEW
- >= 25: ALERT
- < 25: APPROVE

## Déploiement

### Développement
```bash
docker-compose up
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables

- DATABASE_URL
- SECRET_KEY
- DEBUG

## License

Propriétaire - Elna Tech Holding © 2026
