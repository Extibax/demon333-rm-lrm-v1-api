from django.test import TestCase, Client

# Create your tests here.


class ProductTest(TestCase):
    def setUp(self):
        self.client = Client()
        requestObj = {
            "email": "ennio.diaz@cheil.com",
            "password": "!cheil123"
        }
        response = self.client.post(
            '/api/token', requestObj)
        self.assertEqual(response.status_code, 200)
        self.token = response.json()["access"]
        self.headers = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    # region Products
    def test_get_all_products(self):
        response = self.client.get(
            '/products/', **self.headers)
        print("-------------------------------------Get All Products--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)

    def test_get_product_by_id(self):
        response = self.client.get(
            '/products/1498', **self.headers)
        print("-------------------------------------Get Product by Id--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Brand
    def test_get_all_brands(self):
        response = self.client.get(
            '/products/brand', **self.headers)
        print("-------------------------------------Get All Brands--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Division
    def test_get_all_divisions(self):
        response = self.client.get(
            '/products/divisions', **self.headers)
        print("-------------------------------------Get All Divisions--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Group
    def test_get_all_groups(self):
        response = self.client.get(
            '/products/group', **self.headers)
        print("-------------------------------------Get All Groups--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Product Types
    def test_get_all_product_types(self):
        response = self.client.get(
            '/products/product_types', **self.headers)
        print("-------------------------------------Get All Product Types--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Range
    def test_get_all_ranges(self):
        response = self.client.get(
            '/products/range', **self.headers)
        print("-------------------------------------Get All Ranges--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Segment
    def test_get_all_segments(self):
        response = self.client.get(
            '/products/segment', **self.headers)
        print("-------------------------------------Get All Segments--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion
