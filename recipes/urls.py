from django.urls import path

from . import views

urlpatterns = [
    path("cuisines/", views.CuisineListView.as_view()),
    path("cuisines/<int:pk>/", views.CuisineDetailView.as_view()),
    path("cuisines/<int:pk>/recipes/", views.CuisineRecipesView.as_view()),
    path("authors/", views.AuthorListView.as_view()),
    path("authors/<int:pk>/", views.AuthorDetailView.as_view()),
    path("authors/<int:pk>/recipes/", views.AuthorRecipesView.as_view()),
    path("recipes/", views.RecipeListView.as_view()),
    path("recipes/<int:pk>/", views.RecipeDetailView.as_view()),
]
