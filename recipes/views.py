from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import error_response
from .models import Author, Cuisine, Recipe
from .serializers import (
    AuthorSerializer,
    CuisineSerializer,
    RecipeListSerializer,
    RecipeSerializer,
)

SORT_OPTIONS = {
    "title": "title",
    "time": "cooking_time",
    "newest": "-created_at",
}


class CuisineListView(APIView):
    def get(self, request):
        cuisines = Cuisine.objects.all()
        serializer = CuisineSerializer(cuisines, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CuisineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CuisineDetailView(APIView):
    def get(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        serializer = CuisineSerializer(cuisine)
        return Response(serializer.data)

    def patch(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        serializer = CuisineSerializer(cuisine, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        try:
            cuisine.delete()
        except ProtectedError:
            count = cuisine.recipes.count()
            return error_response(
                f"Неможливо видалити кухню, бо в ній є рецепти ({count}). "
                "Спершу видаліть їх або перенесіть в іншу кухню.",
                status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CuisineRecipesView(APIView):
    def get(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        serializer = RecipeListSerializer(cuisine.recipes.all(), many=True)
        return Response(serializer.data)


class AuthorListView(APIView):
    def get(self, request):
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AuthorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AuthorDetailView(APIView):
    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = AuthorSerializer(author)
        return Response(serializer.data)

    def patch(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = AuthorSerializer(author, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        try:
            author.delete()
        except ProtectedError:
            count = author.recipes.count()
            return error_response(
                f"Неможливо видалити автора, бо за ним закріплено "
                f"рецепти ({count}). Спершу видаліть їх або "
                "призначте їм іншого автора.",
                status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthorRecipesView(APIView):
    def get(self, request, pk):
        author = get_object_or_404(Author, pk=pk)
        serializer = RecipeListSerializer(author.recipes.all(), many=True)
        return Response(serializer.data)


class RecipeListView(APIView):
    def get(self, request):
        recipes = Recipe.objects.all()
        params = request.query_params

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

    def post(self, request):
        serializer = RecipeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeDetailView(APIView):
    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data)

    def patch(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = RecipeSerializer(recipe, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
