import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from recipes.models import Author, Cuisine, Ingredient, Recipe, Step

USER_PASSWORD = "Recepty2026!"


@pytest.fixture
def api_client():
    """Клієнт для запитів до API без токена (гість)."""
    return APIClient()


@pytest.fixture
def user():
    """Звичайний користувач."""
    return User.objects.create_user(
        username="cook",
        email="cook@example.com",
        password=USER_PASSWORD,
    )


@pytest.fixture
def admin_user():
    """Адміністратор (is_staff=True)."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password=USER_PASSWORD,
    )


def login(client, username):
    """Входить через API і додає access токен до всіх наступних запитів."""
    response = client.post(
        "/api/auth/login/",
        {"username": username, "password": USER_PASSWORD},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def user_client(user):
    """Клієнт з токеном звичайного користувача."""
    return login(APIClient(), user.username)


@pytest.fixture
def admin_client(admin_user):
    """Клієнт з токеном адміністратора."""
    return login(APIClient(), admin_user.username)


@pytest.fixture
def cuisine():
    return Cuisine.objects.create(name="Українська")


@pytest.fixture
def author():
    return Author.objects.create(name="Олена Коваль")


@pytest.fixture
def recipe(cuisine, author):
    """Готовий рецепт з двома інгредієнтами і двома кроками."""
    recipe = Recipe.objects.create(
        title="Український борщ",
        cuisine=cuisine,
        author=author,
        meal_type="soup",
        difficulty="medium",
        cooking_time=90,
        servings=6,
    )
    Ingredient.objects.create(recipe=recipe, name="Буряк", amount="2 шт")
    Ingredient.objects.create(recipe=recipe, name="Капуста", amount="300 г")
    Step.objects.create(recipe=recipe, number=1, text="Зварити бульйон")
    Step.objects.create(recipe=recipe, number=2, text="Додати овочі")
    return recipe


@pytest.fixture
def recipe_data(cuisine, author):
    """Коректні дані для створення рецепта через POST."""
    return {
        "title": "Сирники",
        "cuisine": cuisine.id,
        "author": author.id,
        "meal_type": "breakfast",
        "difficulty": "easy",
        "cooking_time": 20,
        "servings": 2,
        "ingredients": [
            {"name": "Сир", "amount": "400 г"},
            {"name": "Яйце", "amount": "1 шт"},
        ],
        "steps": [
            {"number": 1, "text": "Змішати сир і яйце"},
            {"number": 2, "text": "Обсмажити"},
        ],
    }
