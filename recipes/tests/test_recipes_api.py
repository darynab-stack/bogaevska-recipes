import pytest
from django.contrib.auth.models import User

from recipes.models import Cuisine, Ingredient, Recipe, Step

pytestmark = pytest.mark.django_db

LIST_URL = "/api/recipes/"


def detail_url(recipe_id):
    return f"/api/recipes/{recipe_id}/"


# Перегляд списку (GET /api/recipes/)


def test_list_is_empty_when_no_recipes(api_client):
    response = api_client.get(LIST_URL)

    assert response.status_code == 200
    assert response.data == []


def test_guest_can_see_recipe_list(api_client, recipe):
    response = api_client.get(LIST_URL)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["title"] == "Український борщ"
    assert "ingredients" not in response.data[0]


def test_search_by_title(api_client, recipe):
    found = api_client.get(LIST_URL, {"search": "борщ"})
    not_found = api_client.get(LIST_URL, {"search": "піца"})

    assert len(found.data) == 1
    assert not_found.data == []


def test_search_by_ingredient_has_no_duplicates(api_client, recipe):
    Ingredient.objects.create(recipe=recipe, name="Маринований буряк", amount="1 шт")

    response = api_client.get(LIST_URL, {"ingredient": "Буряк"})

    assert response.status_code == 200
    assert len(response.data) == 1


def test_filter_by_cuisine_and_max_time(api_client, recipe, author):
    other_cuisine = Cuisine.objects.create(name="Італійська")
    Recipe.objects.create(
        title="Паста",
        cuisine=other_cuisine,
        author=author,
        meal_type="main",
        difficulty="easy",
        cooking_time=20,
        servings=2,
    )

    by_cuisine = api_client.get(LIST_URL, {"cuisine": recipe.cuisine.id})
    by_time = api_client.get(LIST_URL, {"max_time": 30})

    assert [item["title"] for item in by_cuisine.data] == ["Український борщ"]
    assert [item["title"] for item in by_time.data] == ["Паста"]


def test_sort_by_time(api_client, recipe, author):
    Recipe.objects.create(
        title="Салат",
        cuisine=recipe.cuisine,
        author=author,
        meal_type="salad",
        difficulty="easy",
        cooking_time=10,
        servings=2,
    )

    response = api_client.get(LIST_URL, {"sort": "time"})

    assert [item["title"] for item in response.data] == ["Салат", "Український борщ"]


@pytest.mark.parametrize(
    "params",
    [{"max_time": "abc"}, {"cuisine": "abc"}, {"sort": "rating"}],
)
def test_list_with_invalid_params_returns_400(api_client, params):
    response = api_client.get(LIST_URL, params)

    assert response.status_code == 400
    assert response.data["detail"]
    assert response.data["errors"] == {}


# Перегляд одного рецепта (GET /api/recipes/{id}/)


def test_guest_can_see_recipe_with_ingredients_and_steps(api_client, recipe):
    response = api_client.get(detail_url(recipe.id))

    assert response.status_code == 200
    assert response.data["title"] == "Український борщ"
    assert len(response.data["ingredients"]) == 2
    assert [step["number"] for step in response.data["steps"]] == [1, 2]


def test_get_nonexistent_recipe_returns_404(api_client):
    response = api_client.get(detail_url(99999))

    assert response.status_code == 404
    assert response.data["detail"] == "Об'єкт з таким id не знайдено."


# Створення (POST /api/recipes/)


def test_guest_cannot_create_recipe(api_client, recipe_data):
    response = api_client.post(LIST_URL, recipe_data, format="json")

    assert response.status_code == 401
    assert Recipe.objects.count() == 0


def test_create_recipe_with_invalid_token_returns_401(api_client, recipe_data):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")

    response = api_client.post(LIST_URL, recipe_data, format="json")

    assert response.status_code == 401


def test_user_can_create_recipe(user_client, recipe_data):
    response = user_client.post(LIST_URL, recipe_data, format="json")

    assert response.status_code == 201
    assert response.data["title"] == "Сирники"
    recipe = Recipe.objects.get(id=response.data["id"])
    assert recipe.ingredients.count() == 2
    assert recipe.steps.count() == 2


def test_create_recipe_without_title_returns_400(user_client, recipe_data):
    del recipe_data["title"]

    response = user_client.post(LIST_URL, recipe_data, format="json")

    assert response.status_code == 400
    assert "title" in response.data["errors"]


def test_create_recipe_without_ingredients_returns_400(user_client, recipe_data):
    recipe_data["ingredients"] = []

    response = user_client.post(LIST_URL, recipe_data, format="json")

    assert response.status_code == 400
    assert response.data["errors"]["ingredients"] == [
        "Рецепт має містити хоча б один інгредієнт."
    ]
    assert Recipe.objects.count() == 0


@pytest.mark.parametrize(
    "field, value",
    [
        ("difficulty", "super_hard"),
        ("meal_type", "snack"),
        ("cooking_time", 0),
        ("servings", -1),
        ("cuisine", 99999),
    ],
)
def test_create_recipe_with_invalid_value_returns_400(
    user_client, recipe_data, field, value
):
    recipe_data[field] = value

    response = user_client.post(LIST_URL, recipe_data, format="json")

    assert response.status_code == 400
    assert field in response.data["errors"]


# Зміна (PATCH /api/recipes/{id}/)


def test_guest_cannot_update_recipe(api_client, recipe):
    response = api_client.patch(
        detail_url(recipe.id), {"cooking_time": 10}, format="json"
    )

    assert response.status_code == 401
    recipe.refresh_from_db()
    assert recipe.cooking_time == 90


def test_user_can_update_recipe(user_client, recipe):
    response = user_client.patch(
        detail_url(recipe.id), {"cooking_time": 80}, format="json"
    )

    assert response.status_code == 200
    assert response.data["cooking_time"] == 80
    recipe.refresh_from_db()
    assert recipe.cooking_time == 80
    assert recipe.ingredients.count() == 2


def test_update_replaces_ingredients(user_client, recipe):
    response = user_client.patch(
        detail_url(recipe.id),
        {"ingredients": [{"name": "Квасоля", "amount": "200 г"}]},
        format="json",
    )

    assert response.status_code == 200
    assert list(recipe.ingredients.values_list("name", flat=True)) == ["Квасоля"]


def test_update_with_invalid_value_returns_400(user_client, recipe):
    response = user_client.patch(detail_url(recipe.id), {"servings": 0}, format="json")

    assert response.status_code == 400
    assert "servings" in response.data["errors"]


def test_update_nonexistent_recipe_returns_404(user_client):
    response = user_client.patch(detail_url(99999), {"servings": 2}, format="json")

    assert response.status_code == 404


# Видалення (DELETE /api/recipes/{id}/)


def test_guest_cannot_delete_recipe(api_client, recipe):
    response = api_client.delete(detail_url(recipe.id))

    assert response.status_code == 401
    assert Recipe.objects.filter(id=recipe.id).exists()


def test_regular_user_cannot_delete_recipe(user_client, recipe):
    response = user_client.delete(detail_url(recipe.id))

    assert response.status_code == 403
    assert response.data["detail"] == "Видаляти можуть лише адміністратори."
    assert Recipe.objects.filter(id=recipe.id).exists()


def test_admin_can_delete_recipe_with_ingredients_and_steps(admin_client, recipe):
    response = admin_client.delete(detail_url(recipe.id))

    assert response.status_code == 204
    assert not Recipe.objects.filter(id=recipe.id).exists()
    assert Ingredient.objects.count() == 0
    assert Step.objects.count() == 0


def test_admin_delete_nonexistent_recipe_returns_404(admin_client):
    response = admin_client.delete(detail_url(99999))

    assert response.status_code == 404


def test_user_becomes_admin_and_can_delete(user, user_client, recipe):
    User.objects.filter(id=user.id).update(is_staff=True)

    response = user_client.delete(detail_url(recipe.id))

    assert response.status_code == 204
