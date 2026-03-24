import base64
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from recipes.models import (Favorite, Follow, Ingredient, IngredientRecipe,
                            Recipe, ShoppingList)
from users.models import User


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
        model = Ingredient



class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        model = User

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and user.follower.filter(
            following=obj).exists()


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )
        model = IngredientRecipe


class IngredientRecipeWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    author = CustomUserSerializer()
    ingredients = IngredientRecipeSerializer(source='ingredientrecipe_set',
                                             many=True, read_only=True)

    class Meta:
        exclude = ('pub_date',)
        model = Recipe


class RecipeWriteSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer(
        read_only=True, default=CurrentUserDefault())
    image = Base64ImageField()
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
        source='ingredientinrecipe_set',
    )

    class Meta:
        exclude = ('pub_date',)
        read_only_fields = (
            'author',
        )
        model = Recipe

    def validate(self, attrs):
        ingredients = self.initial_data.get('ingredients')
        ingredients_id_list = []
        for ingredient in ingredients:
            ingredients_id_list.append(ingredient.get('id'))
        if not ingredients:
            raise serializers.ValidationError(
                'В рецепте должен быть хотя бы один ингредиент.')
        if len(ingredients_id_list) != len(set(ingredients_id_list)):
            raise serializers.ValidationError('Ингредиенты не должны '
                                              'повторяться.')
        return attrs

    def get_is_favorited(self, obj):
        return Favorite.objects.filter(user=self.context['request'].user,
                                       recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingList.objects.filter(user=self.context['request'].user,
                                           recipe=obj).exists()

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    def _add_ingredients(self, recipe, ingredients):
        data = []
        for ingredient in ingredients:
            data.append(IngredientRecipe(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ))
        IngredientRecipe.objects.bulk_create(data)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredientinrecipe_set')
        recipe = Recipe.objects.create(**validated_data)
        self._add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        ingredients = validated_data.pop('ingredientinrecipe_set')
        instance.ingredients.clear()
        instance.save()
        self._add_ingredients(instance, ingredients)
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        model = Favorite

    def validate(self, data):
        if (self.context['request'].method == "POST"
                and Favorite.objects.filter(
                    user=self.context['request'].user,
                    recipe_id=self.context['recipe_id']
        ).exists()):
            raise serializers.ValidationError(
                'Вы уже добавили в избранное!'
            )
        if (self.context['request'].method == "DELETE" and not
            Favorite.objects.filter(
                user=self.context['request'].user,
                recipe_id=self.context['recipe_id']
        ).exists()):
            raise serializers.ValidationError(
                'Этот рецепт не в избранном.'
            )
        return data


class RecipeShortSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    image = serializers.ImageField(read_only=True)
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        model = Follow

    def validate(self, data):
        if self.context['request'].method == "POST" and Follow.objects.filter(
                user=self.context['request'].user,
                following_id=self.context['user_id']
        ).exists():
            raise serializers.ValidationError(
                'Такая подписка уже есть.'
            )
        if (self.context['request'].method == "POST"
                and self.context['request'].user.id
                == self.context['user_id']):
            raise serializers.ValidationError(
                'На себя нельзя подписаться.'
            )
        if (self.context['request'].method == "DELETE" and not
            Follow.objects.filter(
                user=self.context['request'].user,
                following_id=self.context['user_id']
        ).exists()):
            raise serializers.ValidationError(
                'Такой подписки нет.'
            )
        return data

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit'
        )
        queryset = obj.following.recipes.all()
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        serializer = RecipeShortSerializer(queryset, many=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(user=self.context['request'].user,
                                     following=obj.following).exists()

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()


class ShoppingCardSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = ShoppingList

    def validate(self, data):
        if (self.context['request'].method == "POST"
                and ShoppingList.objects.filter(
                    user=self.context['request'].user,
                    recipe_id=self.context['recipe_id']
        ).exists()):
            raise serializers.ValidationError(
                'Уже добавлен в список покупок.'
            )
        if (self.context['request'].method == "DELETE" and not
            ShoppingList.objects.filter(
                user=self.context['request'].user,
                recipe_id=self.context['recipe_id']
        ).exists()):
            raise serializers.ValidationError(
                'Этого рецепта нет в списке покупок.'
            )
        return data
