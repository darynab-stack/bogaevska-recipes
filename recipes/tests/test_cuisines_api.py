import pytest

from recipes.models import Cuisine

pytestmark = pytest.mark.django_db


def test_guest_can_see_cuisines(api_client, cuisine):
    response = api_client.get("/api/cuisines/")

    assert response.status_code == 200
    assert response.data[0]["name"] == "Українська"


def test_user_can_create_cuisine(user_client):
    response = user_client.post("/api/cuisines/", {"name": "Грецька"}, format="json")

    assert response.status_code == 201
    assert Cuisine.objects.filter(name="Грецька").exists()


def test_create_duplicate_cuisine_returns_400(user_client, cuisine):
    response = user_client.post("/api/cuisines/", {"name": "Українська"}, format="json")

    assert response.status_code == 400
    assert "name" in response.data["errors"]


def test_admin_cannot_delete_cuisine_with_recipes(admin_client, recipe):
    response = admin_client.delete(f"/api/cuisines/{recipe.cuisine.id}/")

    assert response.status_code == 409
    assert "рецепти (1)" in response.data["detail"]
    assert Cuisine.objects.filter(id=recipe.cuisine.id).exists()


def test_admin_can_delete_cuisine_without_recipes(admin_client, cuisine):
    response = admin_client.delete(f"/api/cuisines/{cuisine.id}/")

    assert response.status_code == 204
    assert not Cuisine.objects.filter(id=cuisine.id).exists()


def test_cuisine_recipes(api_client, recipe):
    response = api_client.get(f"/api/cuisines/{recipe.cuisine.id}/recipes/")

    assert response.status_code == 200
    assert [item["title"] for item in response.data] == ["Український борщ"]
