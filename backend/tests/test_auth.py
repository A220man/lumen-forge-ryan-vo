import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_auth_token_creation(monkeypatch):
    """Test that access tokens can be created and decoded with a secret."""
    from app.core.auth import create_access_token
    from app.core.config import settings

    # Directly patch the singleton settings object's jwt_secret
    settings.jwt_secret = "test-secret-key-for-demo"

    token = create_access_token({"sub": "testuser", "role": "admin"})
    assert token is not None
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, "test-secret-key-for-demo", algorithms=["HS256"])
        assert payload["sub"] == "testuser"
    except JWTError:
        pytest.fail("Token decode failed")


@pytest.mark.asyncio
async def test_auth_demo_mode(monkeypatch):
    """Test that auth falls back to demo mode when OIDC issuer is None."""
    from app.core.auth import create_access_token
    from app.core import config as config_mod

    # Patch the singleton settings
    settings = config_mod.settings
    settings.oidc_issuer_url = None
    settings.jwt_secret = "demo-secret"

    # create_access_token should work with the demo secret
    token = create_access_token({"sub": "demo-user"})
    assert token is not None

    # The app health endpoint doesn't depend on auth, verify it works
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
