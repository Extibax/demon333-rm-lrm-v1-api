from django.test import TestCase, Client

# Create your tests here.


class StoreTest(TestCase):
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

    # region Account
    def test_get_all_accounts(self):
        response = self.client.get(
            '/stores/account', **self.headers)
        print("-------------------------------------Get All Accounts--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Point of Sale
    def test_get_all_point_of_sales(self):
        response = self.client.get(
            '/stores/pointOfSales', **self.headers)
        print("-------------------------------------Get All Point of Sales--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)

    def test_get_point_of_sales_by_id(self):
        response = self.client.get(
            '/stores/pointOfSales/1', **self.headers)
        print("-------------------------------------Get Point of Sale by Id--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Pos_Type
    def test_get_all_point_of_sale_types(self):
        response = self.client.get(
            '/stores/pos_type', **self.headers)
        print("-------------------------------------Get All Point of Sales Types--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Segment
    def test_get_all_Segments(self):
        response = self.client.get(
            '/stores/segment', **self.headers)
        print("-------------------------------------Get All Segments--------------------------------------------")
        print(response.json())
        print("----------------------------------------------------------------------------------------------")
        self.assertEqual(response.status_code, 200)
    # endregion
