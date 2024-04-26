"""
Test for recipe API.
"""

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Sample recipe",
        "time_minutes": 10,
        "price": Decimal("5.00"),
        "description": "Sample description",
        "link": "https://sample.com",
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return a sample user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testpass")
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for authenticated user"""
        other_user = create_user(
            email="other@example.com",
            password="testpass",
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating recipe"""
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal("5.00"),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = create_recipe(user=self.user)
        payload = {"title": "Chicken tikka"}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = create_recipe(user=self.user)
        payload = {
            "title": "Spaghetti carbonara",
            "time_minutes": 25,
            "price": Decimal("12.00"),
            "link": "https://sample.com/spaghetti-carbonara",
            "description": "spaghetti carbonara description",
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        """Test changing the recipe user return error"""
        new_user = create_user(email="user2@example.com, password=testpass")
        recipe = create_recipe(user=self.user)
        payload = {"user": new_user}
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 0)

    def test_delete_other_users_recipe_error(self):
        """Test deleting other users recipe return error"""
        other_user = create_user(email="user2@example.com", password="testpass")  # noqa
        recipe = create_recipe(user=other_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 1)

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""

        payload = {
            "title": "Avocado lime cheesecake",
            "tags": [{"name": "vegan"}, {"name": "dessert"}],
            "time_minutes": 60,
            "price": Decimal("20.00"),
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exist = recipe.tags.filter(
                name=tag["name"], user=self.user
            ).exists()  # noqa
            self.assertTrue(exist)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags"""
        tag_vagan = Tag.objects.create(user=self.user, name="vegan")
        payload = {
            "title": "Avocado lime cheesecake",
            "tags": [{"name": "vegan"}, {"name": "dessert"}],
            "time_minutes": 60,
            "price": Decimal("20.00"),
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_vagan, recipe.tags.all())
        for tag in payload["tags"]:
            exist = recipe.tags.filter(
                name=tag["name"], user=self.user
            ).exists()  # noqa
            self.assertTrue(exist)

    def test_create_tag_on_update(self):
        """Test creating a tag on update"""
        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "vegan"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name="vegan", user=self.user)
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning existing tag when updating a recipe"""
        tag1 = Tag.objects.create(user=self.user, name="tag1")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1)

        tag2 = Tag.objects.create(user=self.user, name="tag2")
        payload = {"tags": [{"name": tag2.name}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing recipe tags"""
        tag1 = Tag.objects.create(user=self.user, name="tag1")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag1)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
        self.assertNotIn(tag1, recipe.tags.all())

    def test_create_recipe_with_ingredients(self):
        """Test creating recipe with ingredients"""
        payload = {
            "title": "Sample recipe",
            "ingredients": [{"name": "ingredient1"}, {"name": "ingredient2"}],
            "time_minutes": 10,
            "price": Decimal("5.00"),
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exist = recipe.ingredients.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exist)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating recipe with existing ingredients"""
        ingredient1 = Ingredient.objects.create(
            user=self.user, name="ingredient1"
        )  # noqa
        payload = {
            "title": "Sample recipe",
            "ingredients": [{"name": "ingredient1"}, {"name": "ingredient2"}],
            "time_minutes": 10,
            "price": Decimal("5.00"),
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient1, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exist = recipe.ingredients.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exist)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {"ingredients": [{"name": "Cabbage"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(name="Cabbage", user=self.user)
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test updating a recipe with existing ingredients"""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Cabbage")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name="Salt")
        payload = {"ingredients": [{"name": "Salt"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing all ingredients from a recipe"""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Cabbage")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe1 = create_recipe(user=self.user, title="Recipe 1")
        recipe2 = create_recipe(user=self.user, title="Recipe 2")
        tag1 = Tag.objects.create(user=self.user, name="Vegan")
        tag2 = Tag.objects.create(user=self.user, name="Dessert")
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = create_recipe(user=self.user, title="Recipe 3")

        res = self.client.get(RECIPES_URL, {"tags": f"{tag1.id},{tag2.id}"})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""
        recipe1 = create_recipe(user=self.user, title="Recipe 1")
        recipe2 = create_recipe(user=self.user, title="Recipe 2")
        ingredient1 = Ingredient.objects.create(
            user=self.user, name="Ingredient 1"
        )  # noqa
        ingredient2 = Ingredient.objects.create(
            user=self.user, name="Ingredient 2"
        )  # noqa
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = create_recipe(user=self.user, title="Recipe 3")

        res = self.client.get(
            RECIPES_URL, {"ingredients": f"{ingredient1.id},{ingredient2.id}"}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class RecipeImageUploadTests(TestCase):
    """Test image upload for recipes"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="testpass")
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            image = Image.new("RGB", (10, 10))
            image.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {"image": "notimage"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
