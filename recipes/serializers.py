from rest_framework import serializers

from .models import Author, Cuisine, Ingredient, Recipe, Step


class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ["id", "name", "description", "image"]


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio", "photo"]


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["name", "amount"]


class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ["number", "text"]


class RecipeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "image",
            "cuisine",
            "meal_type",
            "difficulty",
            "cooking_time",
        ]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True)
    steps = StepSerializer(many=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "description",
            "image",
            "cuisine",
            "author",
            "meal_type",
            "difficulty",
            "cooking_time",
            "servings",
            "ingredients",
            "steps",
            "created_at",
        ]

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Рецепт має містити хоча б один інгредієнт."
            )
        return value

    def validate_steps(self, value):
        if not value:
            raise serializers.ValidationError("Рецепт має містити хоча б один крок.")
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        steps_data = validated_data.pop("steps")
        recipe = Recipe.objects.create(**validated_data)
        for item in ingredients_data:
            Ingredient.objects.create(recipe=recipe, **item)
        for item in steps_data:
            Step.objects.create(recipe=recipe, **item)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        steps_data = validated_data.pop("steps", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for item in ingredients_data:
                Ingredient.objects.create(recipe=instance, **item)
        if steps_data is not None:
            instance.steps.all().delete()
            for item in steps_data:
                Step.objects.create(recipe=instance, **item)
        return instance
