import pytest
from django.contrib.auth.models import User

from conftest import USER_PASSWORD

pytestmark = pytest.mark.django_db


@pytest.fixture
def register_data():
    return {
        "username": "olena",
        "first_name": "Олена",
        "email": "olena@example.com",
        "password": USER_PASSWORD,
        "password_confirm": USER_PASSWORD,
    }


def test_register_creates_user_with_hashed_password(api_client, register_data):
    response = api_client.post("/api/auth/register/", register_data, format="json")

    assert response.status_code == 201
    assert "password" not in response.data
    user = User.objects.get(username="olena")
    assert user.password != USER_PASSWORD
    assert user.check_password(USER_PASSWORD)


def test_register_with_different_passwords_returns_400(api_client, register_data):
    register_data["password_confirm"] = "Інший_пароль1"

    response = api_client.post("/api/auth/register/", register_data, format="json")

    assert response.status_code == 400
    assert "password_confirm" in response.data["errors"]


def test_register_with_simple_password_returns_400(api_client, register_data):
    register_data["password"] = register_data["password_confirm"] = "12345678"

    response = api_client.post("/api/auth/register/", register_data, format="json")

    assert response.status_code == 400
    assert "password" in response.data["errors"]


def test_register_with_existing_email_returns_400(api_client, user, register_data):
    register_data["email"] = user.email.upper()

    response = api_client.post("/api/auth/register/", register_data, format="json")

    assert response.status_code == 400
    assert "email" in response.data["errors"]


def test_login_returns_tokens(api_client, user):
    response = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": USER_PASSWORD},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


def test_login_with_wrong_password_returns_401(api_client, user):
    response = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": "wrong-password"},
        format="json",
    )

    assert response.status_code == 401


def test_refresh_returns_new_access_token(api_client, user):
    tokens = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": USER_PASSWORD},
        format="json",
    ).data

    response = api_client.post(
        "/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json"
    )

    assert response.status_code == 200
    assert "access" in response.data


def test_me_without_token_returns_401(api_client):
    response = api_client.get("/api/users/me/")

    assert response.status_code == 401


def test_me_returns_current_user(user_client, user):
    response = user_client.get("/api/users/me/")

    assert response.status_code == 200
    assert response.data["username"] == user.username
    assert response.data["is_staff"] is False
