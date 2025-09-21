# conftest.py
import json
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user(db):
    def _create_user(username="testuser", email="test@example.com", password="password123"):
        return User.objects.create_user(username=username, email=email, password=password)
    return _create_user

# If your /api/predict/ endpoint requires authentication using SimpleJWT:
@pytest.fixture
def auth_client(api_client, create_user):
    user = create_user()
    try:
        # prefer DRF Simple JWT if installed
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    except Exception:
        # fallback: login via API (if you have an auth endpoint)
        logged_in = api_client.post("/api/login/", {"username": user.username, "password": "password123"}, format="json")
        # ensure login worked in your project or adapt accordingly
    return api_client

@pytest.fixture
def load_test_cases():
    def _load(path="tests/test_data.json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return _load
