from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def sample_recipe(user, **params):
    """Creating a sample recipe"""
    defaults={
        'title':'sample recipe',
        'time_minutes':20,
        'price':5.00
    }
    
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)



class PublicTagsApiTest(TestCase):
    """Test the publicly avaliable tags api"""

    def setUp(self):
        self.client = APIClient()

    
    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorized user tags api"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'poop1'
        )
        self.client=APIClient()
        self.client.force_authenticate(self.user)

    def test_retieve_tags(self):
        """Test retrieveing tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)  


    def test_tags_limited_to_user(self):
        """Test tags returned are for the authenticated user"""

        user2 = get_user_model().objects.create_user(
            'abot@gmail.com',
            'abot231'
        )     
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)


    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {'name':'Test Tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    
    def test_create_invalid_tag(self):
        """Test creating new tag with invalid name"""
        payload = {'name':''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    def test_retrieve_tags_assigned_to_recipe(self):
        """Test retrieve tags by those assigned to recipe"""
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')

        recipe = sample_recipe(user=self.user)

        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only':1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    
    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Lunch')
        recipe1 = sample_recipe(user=self.user, title='Eggs and Ham')
        recipe2 = sample_recipe(user=self.user, title='Eggs and Bacon')

        recipe1.tags.add(tag)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only':1})

        self.assertEqual(len(res.data), 1)
