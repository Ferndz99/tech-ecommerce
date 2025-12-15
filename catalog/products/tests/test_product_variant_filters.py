from rest_framework.test import APITestCase
from django.urls import reverse
from catalog.models.product import Product
from catalog.models.product_variant import ProductVariant
from catalog.models.brand import Brand
from catalog.models.category import Category


class ProductVariantFilterTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(name="iPhone")
        cls.category = Category.objects.create(name="Smartphones")

        cls.product_iphone = Product.objects.create(
            name="iPhone 14", brand=cls.brand, category=cls.category
        )

        cls.product_samsung = Product.objects.create(
            name="Galaxy S23", brand=cls.brand, category=cls.category
        )

        cls.variant_cheap = ProductVariant.objects.create(
            product=cls.product_iphone,
            name="iPhone 14 128GB",
            slug="iphone-14-128gb",
            price=800,
            stock=5,
            is_active=True,
            sku="TEST-1",
        )

        cls.variant_expensive = ProductVariant.objects.create(
            product=cls.product_iphone,
            name="iPhone 13 256GB",
            slug="iphone-13-256GB",
            price=1200,
            stock=20,
            is_active=True,
            sku="TEST-2",
        )

        cls.url = reverse("product-variant-list")

    def test_filter_price_min(self):
        response = self.client.get(self.url, {"price_min": 1000})

        self.assertEqual(response.status_code, 200)

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"iphone-13-256GB"})


    def test_filter_price_max(self):
        response = self.client.get(self.url, {"price_max": 900})

        self.assertEqual(response.status_code, 200)

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"iphone-14-128gb"})


    def test_filter_price_range(self):
        response = self.client.get(
            self.url,
            {"price_min": 700, "price_max": 1000},
        )

        self.assertEqual(response.status_code, 200)

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"iphone-14-128gb"})

    def test_filter_stock_min(self):
        response = self.client.get(self.url, {"stock_min": 10})

        self.assertEqual(response.status_code, 200)

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"iphone-13-256GB"})


    def test_filter_stock_max(self):
        response = self.client.get(self.url, {"stock_max": 10})

        self.assertEqual(response.status_code, 200)

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"iphone-14-128gb"})


    def test_filter_is_active_true(self):
        response = self.client.get(self.url, {"is_active": True})

        self.assertEqual(response.status_code, 200)

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(
            slugs,
            {"iphone-14-128gb", "iphone-13-256GB"},
        )


    def test_filter_by_slug(self):
        response = self.client.get(
            self.url,
            {"slug": "iphone-14-128gb"},
        )
    
        self.assertEqual(response.status_code, 200)
    
        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"iphone-14-128gb"})


    def test_filter_by_name(self):
        response = self.client.get(
            self.url,
            {"name": "iPhone 13 256GB"},
        )

        self.assertEqual(response.status_code, 200)

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"iphone-13-256GB"})

    def test_filter_price_and_stock(self):
        response = self.client.get(
            self.url,
            {
                "price_min": 1000,
                "stock_min": 15,
            },
        )
    
        self.assertEqual(response.status_code, 200)
    
        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"iphone-13-256GB"})





