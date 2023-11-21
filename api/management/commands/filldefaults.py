from django.core.management.base import BaseCommand, CommandError
#from api.models import Question as Poll
from administration.models import Role

from product.models import Group
from product.models import Division
from product.models import Brand
from product.models import Range
from product.models import Segment as ProductSegment
from product.models import Week

from store.models import Segment as StoreSegment
from store.models import PointOfSaleType
from store.models import Account

from locations.models import CountryGroup
from locations.models import Country
from locations.models import Region
from locations.models import CountryZone
from locations.models import City


class Command(BaseCommand):
    help = 'creates defaults 0 in all strong models'

    # def add_arguments(self, parser):
    #    parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        ########################################################################
        # Administration Models
        ########################################################################

        try:
            self.stdout.write("Creating superuser role")
            Role(id=1, status=True, role_name="superuser").save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        ########################################################################
        # Product Models
        ########################################################################
        try:
            self.stdout.write("Creating default product group")
            obj = Group(id=1, value="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating default product division")
            obj = Division(id=1, value="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(
                f"\tdefault product Division {ex}")

        try:
            self.stdout.write("Creating default product brand")
            obj = Brand(id=1, value="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating default product range")
            obj = Range(id=1, value="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating default product segment")
            obj = ProductSegment(id=1, value="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating default week objects")
            for y in range(2019, 2030+1):
                for w in range(1, 52+1):
                    Week(year=y, week=w).save()

        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        ########################################################################
        # Store Models
        ########################################################################

        try:
            self.stdout.write("Creating default StoreSegment")
            obj = StoreSegment(id=1, value="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating default PointOfSaleType")
            obj = PointOfSaleType(id=1, value="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating default Account")
            obj = Account(id=1, name="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        ########################################################################
        # Location Models
        ########################################################################

        try:
            self.stdout.write("Creating default CountryGroup")
            obj = CountryGroup(id=1, name="default")
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")

        try:
            self.stdout.write("Creating default Country")
            obj = Country(id=1, code="NA", name="default")
            obj.save()
            obj.group.add(CountryGroup.objects.get(id=1))

        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating default Region")
            obj = Region(id=1, name="default",
                         country=Country.objects.get(id=1))

            obj.save()

        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating default CountryZone")
            obj = CountryZone(id=1, name="default",
                              region=Region.objects.get(id=1))
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
        try:
            self.stdout.write("Creating default City")
            obj = City(id=1, name="default",
                       zone=CountryZone.objects.get(id=1))
            obj.save()
        except Exception as ex:
            self.stdout.write(f"\t{ex}")
