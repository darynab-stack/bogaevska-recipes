from django.core.validators import MinValueValidator
from django.db import models


class Cuisine(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    photo = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = "breakfast", "сніданок"
        SOUP = "soup", "суп"
        MAIN = "main", "основна страва"
        SALAD = "salad", "салат"
        DESSERT = "dessert", "десерт"
        DRINK = "drink", "напій"

    class Difficulty(models.TextChoices):
        EASY = "easy", "легко"
        MEDIUM = "medium", "середньо"
        HARD = "hard", "складно"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.URLField(blank=True)
    meal_type = models.CharField(max_length=20, choices=MealType.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    cooking_time = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    servings = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    cuisine = models.ForeignKey(
        Cuisine, on_delete=models.PROTECT, related_name="recipes"
    )
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name="recipes")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Ingredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredients"
    )
    name = models.CharField(max_length=100)
    amount = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.amount})"


class Step(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="steps")
    number = models.PositiveIntegerField()
    text = models.TextField()

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. {self.text[:30]}"
