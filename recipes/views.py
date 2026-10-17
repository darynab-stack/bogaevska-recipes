from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cuisine
from .serializers import CuisineSerializer, RecipeListSerializer


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
            return Response(
                {
                    "detail": (
                        f"Неможливо видалити кухню, бо в ній є рецепти ({count}). "
                        "Спершу видаліть їх або перенесіть в іншу кухню."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CuisineRecipesView(APIView):
    def get(self, request, pk):
        cuisine = get_object_or_404(Cuisine, pk=pk)
        serializer = RecipeListSerializer(cuisine.recipes.all(), many=True)
        return Response(serializer.data)
