from email.policy import default
from tabnanny import verbose
from django.db import models

# Create your models here.


class CountryGroup(models.Model):
    def __str__(self) -> str:
        return f"{self.name}"
    """areas like NCA"""
    name = models.CharField(max_length=30, unique=True)
    #countries = models.ManyToManyField(Country)


class Country(models.Model):
    def __str__(self) -> str:
        return f"{self.name}"
    code = models.CharField(unique=True, max_length=2)
    name = models.CharField(max_length=30, unique=True)
    group = models.ManyToManyField(CountryGroup)
    latitude = models.DecimalField(default=0,decimal_places=10,max_digits = 14)
    longitude = models.DecimalField(default=0,decimal_places=10,max_digits = 14)
    class Meta:
        verbose_name_plural = "Countries"
        verbose_name = "Country"


class Region(models.Model):
    def __str__(self) -> str:
        return f"{self.name}"
    """country zone like provincias centrales"""
    name = models.CharField(max_length=30)
    # country = models.ForeignKey(
    #    Country, related_name='region', on_delete=models.DO_NOTHING)


class CountryZone(models.Model):
    def __str__(self) -> str:
        return f"{self.name}"
    """area like herrera"""
    name = models.CharField(max_length=30)
    # region = models.ForeignKey(
    #    Region, related_name='zone', on_delete=models.DO_NOTHING)


class City(models.Model):
    def __str__(self) -> str:
        return f"{self.name}"
    name = models.CharField(max_length=30, unique=True)
    # zone = models.ForeignKey(
    #    CountryZone, related_name='city', on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name_plural = "Cities"
        verbose_name = "City"
