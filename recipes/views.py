import logging

from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import error_response
from .models import Author, Cuisine, Recipe
from .permissions import IsAdminToDelete
from .serializers import (
    AuthorSerializer,
    CuisineSerializer,
    ErrorSerializer,
    RecipeListSerializer,
    RecipeSerializer,
)

logger = logging.getLogger(__name__)

SORT_OPTIONS = {
    "title": "title",
    "time": "cooking_time",
    "newest": "-created_at",
}

ERROR_400 = OpenApiResponse(ErrorSerializer, description="Дані не пройшли перевірку.")
ERROR_401 = OpenApiResponse(
    ErrorSerializer, description="Немає access токена або він недійсний."
)
ERROR_403 = OpenApiResponse(
    ErrorSerializer, description="Видаляти можуть лише адміністратори."
)
ERROR_404 = OpenApiResponse(ErrorSerializer, description="Об'єкт не знайдено.")
ERROR_409 = OpenApiResponse(
    ErrorSerializer,
    description="Не можна видалити, бо на об'єкт посилаються рецепти.",
)

RECIPE_EXAMPLE = OpenApiExample(
    "Новий рецепт",
    value={
        "title": "Український борщ",
        "description": "Класичний борщ на яловичому бульйоні",
        "cuisine": 1,
        "author": 1,
        "meal_type": "soup",
        "difficulty": "medium",
        "cooking_time": 90,
        "servings": 6,
        "ingredients": [
            {"name": "Буряк", "amount": "2 шт"},
            {"name": "Капуста", "amount": "300 г"},
        ],
        "steps": [
            {"number": 1, "text": "Зварити бульйон"},
            {"number": 2, "text": "Натерти буряк і обсмажити з морквою"},
        ],
    },
    request_only=True,
)

VALIDATION_ERROR_EXAMPLE = OpenApiExample(
    "Рецепт без інгредієнтів",
    value={
        "detail": "Дані не пройшли перевірку. Виправте поля з помилками.",
        "errors": {"ingredients": ["Рецепт має містити хоча б один інгредієнт."]},
    },
    response_only=True,
    status_codes=["400"],
)

FORBIDDEN_EXAMPLE = OpenApiExample(
    "Звичайний користувач",
    value={"detail": "Видаляти можуть лише адміністратори.", "errors": {}},
    response_only=True,
    status_codes=["403"],
)

CONFLICT_EXAMPLE = OpenApiExample(
    "Кухня з рецептами",
    value={
        "detail": "Неможливо видалити кухню, бо в ній є рецепти (3). "
        "Спершу видаліть їх або перенесіть в іншу кухню.",
        "errors": {},
    },
    response_only=True,
    status_codes=["409"],
)


class CuisineListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["Кухні"],
        summary="Список кухонь",
        description="Доступно всім.",
        responses={200: CuisineSerializer(many=True)},
    )
    def get(self, request):
        cuisines = Cuisine.objects.all()
        serializer = CuisineSerializer(cuisines, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Кухні"],
        summary="Додати кухню",
        description="Потрібен access токен.",
        request=CuisineSerializer,
        responses={201: CuisineSerializer, 400: ERROR_400, 401: ERROR_401},
    )
    def post(self, request):
        serializer = CuisineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cuisine = serializer.save()
        logger.info(
            "Користувач %s додав кухню id=%s", request.user.username, cuisine.id
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CuisineDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminToDelete]

    @extend_schema(
        tags=["Кухні"],
        summary="Одна кухня",
        description="Доступно всім.",
        responses={200: CuisineSerializer, 404: ERROR_404},
    )
    def get(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        serializer = CuisineSerializer(cuisine)
        return Response(serializer.data)

    @extend_schema(
        tags=["Кухні"],
        summary="Змінити кухню",
        description="Потрібен access токен. Можна передати лише ті поля, "
        "які треба змінити.",
        request=CuisineSerializer,
        responses={
            200: CuisineSerializer,
            400: ERROR_400,
            401: ERROR_401,
            404: ERROR_404,
        },
    )
    def patch(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        serializer = CuisineSerializer(cuisine, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(
            "Користувач %s змінив кухню id=%s", request.user.username, cuisine.id
        )
        return Response(serializer.data)

    @extend_schema(
        tags=["Кухні"],
        summary="Видалити кухню",
        description="Лише для адміністраторів. Кухню, в якій є рецепти, "
        "видалити не можна.",
        responses={
            204: None,
            401: ERROR_401,
            403: ERROR_403,
            404: ERROR_404,
            409: ERROR_409,
        },
        examples=[FORBIDDEN_EXAMPLE, CONFLICT_EXAMPLE],
    )
    def delete(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        try:
            cuisine.delete()
        except ProtectedError:
            count = cuisine.recipes.count()
            logger.warning(
                "Не вдалося видалити кухню id=%s: у ній є рецепти (%s)",
                pk,
                count,
            )
            return error_response(
                f"Неможливо видалити кухню, бо в ній є рецепти ({count}). "
                "Спершу видаліть їх або перенесіть в іншу кухню.",
                status.HTTP_409_CONFLICT,
            )
        logger.info("Користувач %s видалив кухню id=%s", request.user.username, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CuisineRecipesView(APIView):
    @extend_schema(
        tags=["Кухні"],
        summary="Рецепти кухні",
        description="Доступно всім.",
        responses={200: RecipeListSerializer(many=True), 404: ERROR_404},
    )
    def get(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        serializer = RecipeListSerializer(cuisine.recipes.all(), many=True)
        return Response(serializer.data)


class AuthorListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["Автори"],
        summary="Список авторів",
        description="Доступно всім.",
        responses={200: AuthorSerializer(many=True)},
    )
    def get(self, request):
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Автори"],
        summary="Додати автора",
        description="Потрібен access токен.",
        request=AuthorSerializer,
        responses={201: AuthorSerializer, 400: ERROR_400, 401: ERROR_401},
    )
    def post(self, request):
        serializer = AuthorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        author = serializer.save()
        logger.info(
            "Користувач %s додав автора id=%s", request.user.username, author.id
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AuthorDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminToDelete]

    @extend_schema(
        tags=["Автори"],
        summary="Один автор",
        description="Доступно всім.",
        responses={200: AuthorSerializer, 404: ERROR_404},
    )
    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = AuthorSerializer(author)
        return Response(serializer.data)

    @extend_schema(
        tags=["Автори"],
        summary="Змінити автора",
        description="Потрібен access токен. Можна передати лише ті поля, "
        "які треба змінити.",
        request=AuthorSerializer,
        responses={
            200: AuthorSerializer,
            400: ERROR_400,
            401: ERROR_401,
            404: ERROR_404,
        },
    )
    def patch(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = AuthorSerializer(author, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(
            "Користувач %s змінив автора id=%s", request.user.username, author.id
        )
        return Response(serializer.data)

    @extend_schema(
        tags=["Автори"],
        summary="Видалити автора",
        description="Лише для адміністраторів. Автора, за яким закріплені "
        "рецепти, видалити не можна.",
        responses={
            204: None,
            401: ERROR_401,
            403: ERROR_403,
            404: ERROR_404,
            409: ERROR_409,
        },
    )
    def delete(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        try:
            author.delete()
        except ProtectedError:
            count = author.recipes.count()
            logger.warning(
                "Не вдалося видалити автора id=%s: за ним закріплені рецепти (%s)",
                pk,
                count,
            )
            return error_response(
                f"Неможливо видалити автора, бо за ним закріплено "
                f"рецепти ({count}). Спершу видаліть їх або "
                "призначте їм іншого автора.",
                status.HTTP_409_CONFLICT,
            )
        logger.info("Користувач %s видалив автора id=%s", request.user.username, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthorRecipesView(APIView):
    @extend_schema(
        tags=["Автори"],
        summary="Рецепти автора",
        description="Доступно всім.",
        responses={200: RecipeListSerializer(many=True), 404: ERROR_404},
    )
    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = RecipeListSerializer(author.recipes.all(), many=True)
        return Response(serializer.data)


class RecipeListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["Рецепти"],
        summary="Список рецептів",
        description="Доступно всім. Підтримує пошук, фільтри і сортування. "
        "Усі параметри необов'язкові, їх можна поєднувати.",
        parameters=[
            OpenApiParameter("search", str, description="Пошук за назвою"),
            OpenApiParameter("ingredient", str, description="Пошук за інгредієнтом"),
            OpenApiParameter("cuisine", int, description="id кухні"),
            OpenApiParameter(
                "meal_type",
                str,
                enum=[choice[0] for choice in Recipe.MealType.choices],
                description="Тип страви",
            ),
            OpenApiParameter(
                "difficulty",
                str,
                enum=[choice[0] for choice in Recipe.Difficulty.choices],
                description="Складність",
            ),
            OpenApiParameter(
                "max_time", int, description="Максимальний час приготування, хв"
            ),
            OpenApiParameter(
                "sort",
                str,
                enum=list(SORT_OPTIONS),
                description="title: за назвою, time: спочатку найшвидші, "
                "newest: спочатку нові",
            ),
        ],
        responses={
            200: RecipeListSerializer(many=True),
            400: OpenApiResponse(
                ErrorSerializer,
                description="cuisine або max_time не число, або невідоме sort.",
            ),
        },
    )
    def get(self, request):
        recipes = Recipe.objects.all()
        params = request.query_params
        logger.debug("Пошук рецептів з параметрами %s", dict(params))

        search = params.get("search")
        if search:
            recipes = recipes.filter(title__icontains=search)

        ingredient = params.get("ingredient")
        if ingredient:
            recipes = recipes.filter(ingredients__name__icontains=ingredient).distinct()

        cuisine = params.get("cuisine")
        if cuisine:
            if not cuisine.isdigit():
                return error_response(
                    "Параметр cuisine має бути числом (id кухні).",
                    status.HTTP_400_BAD_REQUEST,
                )
            recipes = recipes.filter(cuisine_id=cuisine)

        meal_type = params.get("meal_type")
        if meal_type:
            recipes = recipes.filter(meal_type=meal_type)

        difficulty = params.get("difficulty")
        if difficulty:
            recipes = recipes.filter(difficulty=difficulty)

        max_time = params.get("max_time")
        if max_time:
            if not max_time.isdigit():
                return error_response(
                    "Параметр max_time має бути числом (хвилини).",
                    status.HTTP_400_BAD_REQUEST,
                )
            recipes = recipes.filter(cooking_time__lte=max_time)

        sort = params.get("sort")
        if sort:
            if sort not in SORT_OPTIONS:
                return error_response(
                    "Невідоме сортування. Можна: " + ", ".join(SORT_OPTIONS),
                    status.HTTP_400_BAD_REQUEST,
                )
            recipes = recipes.order_by(SORT_OPTIONS[sort])

        serializer = RecipeListSerializer(recipes, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Рецепти"],
        summary="Додати рецепт",
        description="Потрібен access токен. У рецепті має бути хоча б один "
        "інгредієнт і хоча б один крок, cooking_time і servings не менше 1.",
        request=RecipeSerializer,
        responses={201: RecipeSerializer, 400: ERROR_400, 401: ERROR_401},
        examples=[RECIPE_EXAMPLE, VALIDATION_ERROR_EXAMPLE],
    )
    def post(self, request):
        serializer = RecipeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        logger.info(
            "Користувач %s додав рецепт id=%s", request.user.username, recipe.id
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminToDelete]

    @extend_schema(
        tags=["Рецепти"],
        summary="Один рецепт",
        description="Доступно всім. Містить інгредієнти і кроки.",
        responses={200: RecipeSerializer, 404: ERROR_404},
    )
    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data)

    @extend_schema(
        tags=["Рецепти"],
        summary="Змінити рецепт",
        description="Потрібен access токен. Можна передати лише ті поля, які "
        "треба змінити. Якщо передати ingredients або steps, старий список "
        "повністю заміниться новим.",
        request=RecipeSerializer,
        responses={
            200: RecipeSerializer,
            400: ERROR_400,
            401: ERROR_401,
            404: ERROR_404,
        },
        examples=[
            OpenApiExample("Змінити час", value={"cooking_time": 80}, request_only=True)
        ],
    )
    def patch(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeSerializer(recipe, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(
            "Користувач %s змінив рецепт id=%s (поля: %s)",
            request.user.username,
            recipe.id,
            ", ".join(request.data),
        )
        return Response(serializer.data)

    @extend_schema(
        tags=["Рецепти"],
        summary="Видалити рецепт",
        description="Лише для адміністраторів. Інгредієнти й кроки "
        "видаляються разом з рецептом.",
        responses={204: None, 401: ERROR_401, 403: ERROR_403, 404: ERROR_404},
        examples=[FORBIDDEN_EXAMPLE],
    )
    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        recipe.delete()
        logger.info("Користувач %s видалив рецепт id=%s", request.user.username, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
