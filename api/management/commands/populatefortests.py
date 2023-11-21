
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

from administration.models import Role, User

from product.models import Group, WeeklySale
from product.models import Division
from product.models import Brand
from product.models import Range
from product.models import Segment as ProductSegment
from product.models import Week
from product.models import Product

from store.models import Segment as StoreSegment
from store.models import PointOfSaleType
from store.models import Account
from store.models import PointOfSale

from locations.models import CountryGroup
from locations.models import Country
from locations.models import Region
from locations.models import CountryZone
from locations.models import City

from random import random


class Command(BaseCommand):
    help = 'creates tests data in all needed models'

    def handle(self, *args, **options):
        #########################################################
        # Acess & Filtering level tests
        #########################################################

        try:
            self.stdout.write("Creating test role")
            Role(id=2, status=True, role_name="test").save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        # create test items

        # region Product Models

        try:
            self.stdout.write("Creating test product group")
            group = Group(id=1, value="test")
            group.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating test product division")
            division = Division(id=2, value="test")
            division.save()
        except Exception as ex:
            self.stdout.write(
                f"\ttest product Division {ex}")

        try:
            self.stdout.write("Creating test product brand")
            brand = Brand(id=2, value="test")
            brand.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating test product range")
            prod_range = Range(id=2, value="test")
            prod_range.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating test product segment")
            prod_segment = ProductSegment(id=2, value="test")
            prod_segment.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            product = Product(
                id=1,
                sku="TEST-SKU",
                marketing_name="TEST PRODUCT",
                end_of_production=datetime.now(),
                brand=brand,
                segment=prod_segment,
                product_range=prod_range,
                division=division,
                group=group,
            )
            product.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        # endregion

        # region Location Models

        try:
            self.stdout.write("Creating test CountryGroup")
            obj = CountryGroup(id=2, name="test")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating test Country")
            obj = Country(id=2, code="TE", name="test")
            obj.save()
            obj.group.add(CountryGroup.objects.get(id=2))

        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating test Region")
            obj = Region(id=2, name="test",
                         country=Country.objects.get(id=2))

            obj.save()

        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating test CountryZone")
            obj = CountryZone(id=2, name="test",
                              region=Region.objects.get(id=2))
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating test City")
            city = City(id=2, name="test",
                        zone=CountryZone.objects.get(id=2))
            city.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        # endregion

        # region Store Models

        try:
            self.stdout.write("Creating test StoreSegment")
            segment = StoreSegment(id=2, value="test")
            segment.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating test PointOfSaleType")
            postype = PointOfSaleType(id=2, value="test")
            postype.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating test Account")
            account = Account(id=2, name="test")
            account.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating test POS")
            pos = PointOfSale(
                id=1,
                site_id="TEST-SITEID",
                gscn_site_name="test pos",
                pos_type=postype,
                city=city,
                segment=segment,
                account=account
            )
            pos.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        # endregion

        # region ASSIGN TEST ACCESS TO TEST ROLES
        try:
            self.stdout.write(f"assigning test access to test role")
            test_role: Role = Role.objects.get(pk=2)

            test_role.countries.add(2)
            test_role.point_of_sales.add(1)
            test_role.accounts.add(2)
            test_role.divisions.add(2)

            User.objects.get(pk=1).roles.add(2)
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        # endregion

        #########################################################
        # Service level tests
        #########################################################

        # region weekly sales

        # for dead inventory

        for w in range(1, 12+8):
            y = 2022
            week_object = Week.objects.get(year=y, week=w)
            self.stdout.write(f"Creating weekly sale {week_object} {y} {w}")
            try:
                sale: WeeklySale = WeeklySale(
                    year=y,
                    week=w,
                    week_object=week_object,
                    first_date_of_week=datetime.now(),
                    site_id=pos,
                    product=product,
                    sold_units=0,
                    inventory=5,
                )
                sale.save()

            except Exception as ex:
                self.stdout.write(f"\t{ex}")

        # endregion
