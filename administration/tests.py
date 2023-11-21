from django.test import TestCase, Client

# Create your tests here.
client = Client()
requestObj = {
    "email": "eivar.m@cheil.com",
    "password": "EEmp10200!"
}


class Case(TestCase):
    def fetch_deadinventory(self, group, filters=""):
        extra_headers = {"HTTP_API-VERSION": "1.1"}
        headers = {**self.headers, **extra_headers}
        response = client.get(
            f"/reports/deadInventoryV2/{group}{filters}", **headers)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def fetch_filters(self):
        extra_headers = {"HTTP_API-VERSION": "1.1"}
        headers = {**self.headers, **extra_headers}
        response = client.get(
            f"/reports/filters/weeklysales", **headers)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def filtering_combinations(self):
        extra_headers = {"HTTP_API-VERSION": "1.1"}
        headers = {**self.headers, **extra_headers}
        response = client.get(
            f"/reports/combinations", **headers)
        return response.json()

    def setUp(self):

        response = client.post(
            '/api/token', requestObj)
        self.assertEqual(response.status_code, 200)
        self.token = response.json()["access"]
        self.headers = {
            'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

        self.user_data = client.get(
            "/api/v1/users/me", follow=True, **self.headers).json()

        self.countries = set()
        self.point_of_sales = set()
        self.views = set()
        self.accounts = set()
        self.divisions = set()

        self.countries_values = set()
        self.point_of_sales_values = set()
        self.views_values = set()
        self.accounts_values = set()
        self.divisions_values = set()

        for role in self.user_data["roles"]:
            for country in role["countries"]:
                self.countries.add(country["id"])
                self.countries_values.add(country["name"])
            for pos in role["point_of_sales"]:
                self.point_of_sales.add(pos["id"])
                self.point_of_sales_values.add(pos["site_id"])
            for view in role["views"]:
                self.views.add(view["id"])
                self.views_values.add(view["name"])
            for account in role["accounts"]:
                self.accounts.add(account["id"])
                self.accounts_values.add(account["name"])
            for division in role["divisions"]:
                self.divisions.add(division["id"])
                self.divisions_values.add(division["value"])


class AccessTest(Case):

    def test_deadinventory(self):
        for item in self.fetch_deadinventory("account__name"):
            self.assertIn(item["account__name"], self.accounts_values)
        for item in self.fetch_deadinventory("division__value"):
            self.assertIn(item["division__value"], self.divisions_values)
        for item in self.fetch_deadinventory("site_id"):
            self.assertIn(item["site_id"], self.point_of_sales_values)
        for item in self.fetch_deadinventory("country__name"):
            self.assertIn(
                item["country__name"], self.countries_values)

    def test_filters(self):
        data = self.fetch_filters()

        accounts = [x["id"] for x in data["accounts"]]
        countries = [x["id"] for x in data["countries"]]
        divisions = [x["id"] for x in data["divisions"]]

        for account in accounts:
            self.assertIn(account, self.accounts)
        for division in divisions:
            self.assertIn(division, self.divisions)
        for country in countries:
            self.assertIn(country, self.countries)

        #self.assertIn(item["account__name"], self.accounts_values)


class FilterTest(Case):

    def test_deadinventory(self):
        print("[FILTERING TEST] Dead Inventory")
        groups = [
            {"path": "account", "query": "point_of_sale_account"},
            {"path": "division", "query": "product_division"},
            {"path": "group", "query": "product_group"},
            # "site_id",
            # "country__name"
        ]
        for group in groups:

            for combination in self.filtering_combinations():

                if combination == "" or not group["query"] in combination:
                    # skip useless combinations
                    continue

                data = self.fetch_deadinventory(group["path"], "?"+combination)
                splitted_group = [x.split("=") for x in combination.split("&")]
                _, value = [
                    x for x in splitted_group if x[0] == group["query"]][0]
                different_data = [
                    x for x in data if x[group["path"]] != int(value)]

                self.assertEquals(len(different_data), 0)


class CalculationTest(Case):

    def test_deadinventory(self):
        print("[CALCULATION TEST] Dead Inventory")

        data = self.fetch_deadinventory("account")

        total_dead_inventory = [x["inventory"]
                                for x in data if x["account"] == 2 and x["is_dead"]]
        self.assertEqual(sum(total_dead_inventory), 60)
        self.assertEqual(len(total_dead_inventory), 12)


class AdministrationTest(Case):

    # region Roles Tests
    def test_get_all_roles(self):
        response = client.get(
            '/administration/roles', **self.headers)
        self.assertEqual(response.status_code, 200)

    def test_get_role_by_id(self):
        response = client.get(
            '/administration/roles/1', **self.headers)
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Users Tests
    def test_get_all_users(self):
        response = client.get(
            '/api/v1/users/', **self.headers)
        self.assertEqual(response.status_code, 200)

    def test_get_current_user(self):
        response = client.get(
            '/api/v1/users/me/', **self.headers)
        self.assertEqual(response.status_code, 200)

    def test_get_user_by_id(self):
        response = client.get(
            '/api/v1/users/1/', **self.headers)
        self.assertEqual(response.status_code, 200)
    # endregion

    # region Action Logs Tests
    def test_get_all_actionlogs(self):
        response = client.get(
            '/administration/actionlog', **self.headers)
        self.assertEqual(response.status_code, 200)
    # endregion
