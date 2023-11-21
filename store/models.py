from django.db import models
from locations.models import City, CountryZone, Region, Country

# Create your models here.


class Segment(models.Model):
    value = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"[Segment {self.id}] {self.value}"


class PointOfSaleType(models.Model):
    """ DC / STORE """
    value = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"[PointOfSaleType {self.id}] {self.value}"


class Account(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"[{self.id}] {self.name}"

class CustomAccountMapping(models.Model):
    original = models.ForeignKey(
        Account, related_name='original_mapping', on_delete=models.DO_NOTHING)
    custom = models.ForeignKey(
        Account, related_name='custom_mapping', on_delete=models.DO_NOTHING)
    store_like = models.CharField(max_length=15, null=False)

    def __str__(self):
        return f"{self.original}->{self.custom}"


class PointOfSale(models.Model):
    # coordinates
    site_id = models.CharField(max_length=50, unique=True)
    gscn_site_name = models.CharField(max_length=100)
    longitude = models.DecimalField(
        default=0, max_digits=20, decimal_places=10)
    latitude = models.DecimalField(default=0, max_digits=20, decimal_places=10)
    mso_name = models.CharField(max_length=100, default="mso_default_name")
    pos_type = models.ForeignKey(
        PointOfSaleType, related_name='pointofsale', on_delete=models.DO_NOTHING)
    city = models.ForeignKey(
        City, related_name='pointofsale', on_delete=models.DO_NOTHING)
    zone = models.ForeignKey(
        CountryZone, related_name='pointofsale', on_delete=models.DO_NOTHING)
    region = models.ForeignKey(
        Region, related_name='pointofsale', on_delete=models.DO_NOTHING)
    country = models.ForeignKey(
        Country, related_name='pointofsale', on_delete=models.DO_NOTHING)
    segment = models.ForeignKey(
        Segment, related_name='pointofsale', on_delete=models.DO_NOTHING)
    account = models.ForeignKey(
        Account, related_name='pointofsale', on_delete=models.DO_NOTHING)
    custom_account = models.ForeignKey(
        Account, related_name='custom_pointofsale', on_delete=models.DO_NOTHING)
    status = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.site_id} ({self.id})"
