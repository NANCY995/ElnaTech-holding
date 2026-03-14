"""
Script pour initialiser les opérateurs Mobile Money
"""
from app.core.database import SessionLocal, engine, Base
from app.models import models  # Import first
from app.models import market   # Import second
from app.models import extended # Import third
from app.models.extended import Operator

# Créer les tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Vérifier si les opérateurs existent déjà
existing = db.query(Operator).count()
if existing > 0:
    print(f"{existing} opérateurs déjà présents")
    db.close()
    exit()

# Opérateurs Mobile Money UEMOA
operators = [
    Operator(
        name="Flooz (Togo)",
        code="flooz",
        cash_in_fee_percent=1.5,
        cash_out_fee_percent=2.0,
        is_active=True
    ),
    Operator(
        name="T-Money (Togo)",
        code="tmoney",
        cash_in_fee_percent=1.0,
        cash_out_fee_percent=1.5,
        is_active=True
    ),
    Operator(
        name="Orange Money",
        code="orange",
        cash_in_fee_percent=1.0,
        cash_out_fee_percent=2.0,
        is_active=True
    ),
    Operator(
        name="Moov Money",
        code="moov",
        cash_in_fee_percent=1.0,
        cash_out_fee_percent=1.5,
        is_active=True
    ),
]

for op in operators:
    db.add(op)

db.commit()
print(f"{len(operators)} opérateurs créés")

db.close()
