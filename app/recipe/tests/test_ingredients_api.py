from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient



from core.models import Ingredient, Recipe


from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def sample_recipe(user, **params):
    defaults = {
        'title':'sample recipe',
        'time_minutes':10,
        'price':8.00
    }

    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicIngredientsApiTests(TestCase):
    """Test the publically available ingredients api"""


    def setUp(self):
        self.client = APIClient()

    
    def test_login_required(self):
        """Test login is required to access the endpoint"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    
class PrivateIngredientsApiTest(TestCase):
    """Test private ingredients API"""


    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test123@gmail.com',
            'test12345'
        )
        self.client.force_authenticate(self.user)


    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name='kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    
    def test_ingredients_limited_to_user(self):
        """Test that ingredients for Auth user are rendered"""

        user2 = get_user_model().objects.create_user(
            'othertest@gmail.com',
            'test123456'
        )

        Ingredient.objects.create(user=user2, name='Potatoes')

        ingredients = Ingredient.objects.create(user=self.user, name='Tomato')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredients.name)


    def test_create_inngredients_successful(self):
        """Test create new ingredient"""
        payload = {'name':'Cabbage'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    
    def test_create_ingredients_invalid(self):
        """Test creating invalid ingredients"""
        payload = {'name':''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    
    def test_retrieve_ingredients_assigned_to_recipe(self):
        """test retrieve ingredients by those assigned to recipe"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Chicken')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Beef')

        recipe = sample_recipe(user=self.user, title='Chicken Stew')

        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only':1})

        serializer1  = IngredientSerializer(ingredient1)
        serializer2  = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)


    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name='Chicken')
        Ingredient.objects.create(user=self.user, name='Beef')

        recipe1 = sample_recipe(user=self.user, title='Chicken Soup')
        recipe2 = sample_recipe(user=self.user, title='Chicken Stew')

        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only':1})

        self.assertEqual(len(res.data), 1)
