from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from ..models import Tag

User = get_user_model()


class TagListAPIViewTests(TestCase):
    """
    Test suite for tags list endpoint (GET /api/tags/).

    Tests cover:
    - Authentication requirements
    - Filtering active tags
    - Ordering by priority and name
    - Response structure
    - Pagination disabled (flat array)
    """

    def setUp(self):
        """Set up test client, test user, and test tags."""
        self.client = APIClient()
        self.tags_url = "/api/tags/"

        # Create test user
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123",
        )

        # Create authentication token
        self.token = Token.objects.create(user=self.user)

        # Create test tags with various configurations
        self.tag_history = Tag.objects.create(
            name="History",
            description="Historical landmarks and museums",
            is_active=True,
            priority=10,
        )

        self.tag_nature = Tag.objects.create(
            name="Nature",
            description="Parks, gardens, and natural attractions",
            is_active=True,
            priority=5,
        )

        self.tag_food = Tag.objects.create(
            name="Food",
            description="Restaurants and culinary experiences",
            is_active=True,
            priority=8,
        )

        # Inactive tag (should not appear in results)
        self.tag_inactive = Tag.objects.create(
            name="Inactive Tag",
            description="This tag is inactive",
            is_active=False,
            priority=100,
        )

        # Tag with same priority as Nature (for name ordering test)
        self.tag_art = Tag.objects.create(
            name="Art",
            description="Art galleries and exhibitions",
            is_active=True,
            priority=5,
        )

    def test_list_tags_success(self):
        """Test successful retrieval of active tags."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

        # Should return only active tags (4 out of 5)
        self.assertEqual(len(response.data), 4)

    def test_list_tags_requires_authentication(self):
        """Test that endpoint requires authentication."""
        # No authentication credentials
        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_list_tags_invalid_token(self):
        """Test that invalid token returns 401."""
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid_token_key")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_tags_response_structure(self):
        """Test that response has correct structure with all required fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check first tag has all required fields
        first_tag = response.data[0]
        self.assertIn("id", first_tag)
        self.assertIn("name", first_tag)
        self.assertIn("description", first_tag)
        self.assertIn("is_active", first_tag)

        # Verify data types
        self.assertIsInstance(first_tag["id"], int)
        self.assertIsInstance(first_tag["name"], str)
        self.assertIsInstance(first_tag["is_active"], bool)

        # All returned tags should be active
        for tag in response.data:
            self.assertTrue(tag["is_active"])

    def test_list_tags_ordering_by_priority(self):
        """Test that tags are ordered by priority (descending) then name (ascending)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Expected order: History (10), Food (8), Art (5), Nature (5)
        # Art comes before Nature because of alphabetical ordering when priority is same
        tag_names = [tag["name"] for tag in response.data]

        self.assertEqual(tag_names[0], "History")  # Priority 10
        self.assertEqual(tag_names[1], "Food")  # Priority 8
        self.assertEqual(tag_names[2], "Art")  # Priority 5, alphabetically first
        self.assertEqual(tag_names[3], "Nature")  # Priority 5, alphabetically second

    def test_list_tags_excludes_inactive(self):
        """Test that inactive tags are not included in response."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify inactive tag is not in results
        tag_names = [tag["name"] for tag in response.data]
        self.assertNotIn("Inactive Tag", tag_names)

        # Verify the inactive tag exists in database
        self.assertTrue(
            Tag.objects.filter(name="Inactive Tag", is_active=False).exists()
        )

    def test_list_tags_no_pagination(self):
        """Test that response is a flat array without pagination."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should be a list, not a paginated object
        self.assertIsInstance(response.data, list)

        # Should not have pagination keys
        self.assertNotIsInstance(response.data, dict)

    def test_list_tags_empty_database(self):
        """Test response when no active tags exist."""
        # Delete all active tags
        Tag.objects.filter(is_active=True).delete()

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        self.assertIsInstance(response.data, list)

    def test_list_tags_with_null_description(self):
        """Test that tags with null description are handled correctly."""
        # Create tag with null description
        tag_no_desc = Tag.objects.create(
            name="No Description", description=None, is_active=True, priority=1
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find the tag in response
        no_desc_tag = next(
            (t for t in response.data if t["name"] == "No Description"), None
        )
        self.assertIsNotNone(no_desc_tag)
        self.assertIsNone(no_desc_tag["description"])

    def test_list_tags_method_not_allowed(self):
        """Test that only GET method is allowed."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Try POST
        response = self.client.post(self.tags_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PUT
        response = self.client.put(self.tags_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try PATCH
        response = self.client.patch(self.tags_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try DELETE
        response = self.client.delete(self.tags_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_list_tags_consistency_across_requests(self):
        """Test that multiple requests return consistent results."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Make multiple requests
        response1 = self.client.get(self.tags_url)
        response2 = self.client.get(self.tags_url)

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Results should be identical
        self.assertEqual(response1.data, response2.data)

    def test_list_tags_with_special_characters(self):
        """Test that tags with special characters in name/description are handled correctly."""
        # Create tag with special characters
        special_tag = Tag.objects.create(
            name="Café & Restaurant",
            description="Places with special chars: ąćęłńóśźż & émojis 🍕",
            is_active=True,
            priority=3,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find the special tag in response
        found_tag = next((t for t in response.data if t["id"] == special_tag.id), None)
        self.assertIsNotNone(found_tag)
        self.assertEqual(found_tag["name"], "Café & Restaurant")
        self.assertIn("🍕", found_tag["description"])

    def test_list_tags_read_only(self):
        """Test that serializer fields are read-only (cannot be modified via this endpoint)."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # This is implicitly tested by method_not_allowed test,
        # but we verify the endpoint is truly read-only
        initial_count = Tag.objects.count()

        response = self.client.get(self.tags_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Count should remain the same
        self.assertEqual(Tag.objects.count(), initial_count)
