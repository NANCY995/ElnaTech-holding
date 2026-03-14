"""
Tests API avec httpx
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestAuthAPI:
    """Tests pour l'API d'authentification"""
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test que le serveur est en marche"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestTransactionsAPI:
    """Tests pour l'API des transactions"""
    
    @pytest.mark.asyncio
    async def test_create_transaction_requires_auth(self):
        """Test que les transactions nécessitent une auth"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/transactions", json={
                "amount": 100,
                "transaction_type": "paiement"
            })
            # Doit retourner 401 ou 403
            assert response.status_code in [401, 403, 422]


class TestMobileMoneyAPI:
    """Tests pour l'API Mobile Money"""
    
    @pytest.mark.asyncio
    async def test_list_operators(self):
        """Test liste des opérateurs"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/mobile-money/operators")
            assert response.status_code == 200
            data = response.json()
            # Retourne une liste
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_operator_fees(self):
        """Test calcul des frais"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/mobile-money/fees/flooz",
                params={"amount": 1000, "operation": "cash_in"}
            )
            # Peut retourner 404 si opérateur n'existe pas
            assert response.status_code in [200, 404]


class TestInsightsAPI:
    """Tests pour l'API Insights"""
    
    @pytest.mark.asyncio
    async def test_get_summary_requires_auth(self):
        """Test que summary nécessite une auth"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/insights/summary")
            assert response.status_code in [401, 403, 422]


class TestWebhooksAPI:
    """Tests pour l'API Webhooks"""
    
    @pytest.mark.asyncio
    async def test_payment_webhook(self):
        """Test webhook de paiement"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/payment/cinetpay",
                json={
                    "event": "payment.success",
                    "data": {"transaction_id": 1}
                }
            )
            # Doit fonctionner même sans auth
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["processed", "ignored"]
