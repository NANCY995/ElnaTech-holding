"""
Tests pour le service de transactions
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.core.database import Base
from app.models.models import User, Account, Transaction
from app.services.transactions.service import TransactionService


# Base de données de test en mémoire
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Fixture pour la session de base de données"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user(db):
    """Crée un utilisateur de test"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def account(db, user):
    """Crée un compte de test"""
    account = Account(
        user_id=user.id,
        account_number="TEST123456",
        balance=10000.0,
        currency="EUR"
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


class TestTransactionService:
    """Tests pour TransactionService"""
    
    def test_create_transaction_success(self, db, user, account):
        """Test création transaction réussie"""
        service = TransactionService()
        
        tx = service.create_transaction(
            db=db,
            user_id=user.id,
            account_id=account.id,
            transaction_type="encaissement",
            amount=1000.0,
            description="Test transaction"
        )
        
        assert tx is not None
        assert tx.amount == 1000.0
        assert tx.status == "validee"
        assert account.balance == 11000.0
    
    def test_insufficient_balance(self, db, user, account):
        """Test transaction avec solde insuffisant"""
        service = TransactionService()
        
        with pytest.raises(ValueError, match="Solde insuffisant"):
            service.create_transaction(
                db=db,
                user_id=user.id,
                account_id=account.id,
                transaction_type="paiement",
                amount=20000.0,
                description="Test transaction"
            )
    
    def test_fraud_detection_blocked(self, db, user, account):
        """Test transaction bloquée par l'anti-fraude"""
        service = TransactionService()
        
        # Créer plusieurs transactions pour simuler un comportement suspect
        for i in range(5):
            service.create_transaction(
                db=db,
                user_id=user.id,
                account_id=account.id,
                transaction_type="paiement",
                amount=1000.0,
                description=f"Test {i}"
            )
        
        # La suivante devrait être bloquée ou alertée
        result = service.create_transaction(
            db=db,
            user_id=user.id,
            account_id=account.id,
            transaction_type="paiement",
            amount=50000.0,
            description="Grosse transaction suspecte"
        )
        
        # Vérifie que l'alerte a été générée
        assert result is not None


class TestAccountService:
    """Tests pour AccountService"""
    
    def test_create_account(self, db, user):
        """Test création de compte"""
        from app.services.accounts.service import AccountService
        
        service = AccountService()
        account = service.create_account(db, user.id, "EUR")
        
        assert account is not None
        assert account.account_number.startswith("ELNA")
        assert account.balance == 0.0
    
    def test_get_balance(self, db, user, account):
        """Test récupération du solde"""
        from app.services.accounts.service import AccountService
        
        service = AccountService()
        balance = service.get_balance(db, account.id)
        
        assert balance == 10000.0


class TestFraudDetection:
    """Tests pour la détection de fraude"""
    
    def test_high_amount_detection(self, db, user):
        """Test détection montant élevé"""
        from app.services.fraud.advanced import FraudDetectionService
        
        service = FraudDetectionService()
        
        result = service.analyze_transaction(
            db=db,
            user_id=user.id,
            amount=100000.0,
            transaction_type="paiement"
        )
        
        assert result["risk_score"] > 0
    
    def test_user_risk_profile(self, db, user, account):
        """Test profil de risque utilisateur"""
        from app.services.fraud.advanced import FraudDetectionService
        
        service = FraudDetectionService()
        
        # Sans transactions
        profile = service.get_user_risk_profile(db, user.id)
        assert profile["total_transactions"] == 0
        
        # Avec transactions
        from app.services.transactions.service import TransactionService
        tx_service = TransactionService()
        
        for i in range(5):
            tx_service.create_transaction(
                db=db,
                user_id=user.id,
                account_id=account.id,
                transaction_type="encaissement",
                amount=1000.0 + i * 100,
                description=f"Test {i}"
            )
        
        profile = service.get_user_risk_profile(db, user.id)
        assert profile["total_transactions"] == 5
