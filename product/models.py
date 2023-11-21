from django.db import models
from store.models import PointOfSale

# Create your models here.


class Group(models.Model):
    value = models.CharField(
        max_length=30, unique=True, blank=False, null=False)

    def __str__(self):
        return f"{self.value}"


class Division(models.Model):
    value = models.CharField(
        max_length=30, unique=True, blank=False, null=False)

    def __str__(self):
        return f"{self.value}"


class Brand(models.Model):
    value = models.CharField(
        max_length=30, unique=True, blank=False, null=False, default="Samsung")

    def __str__(self):
        return f"[Brand {self.id}] {self.value}"


class Range(models.Model):
    value = models.CharField(
        max_length=30, unique=True, blank=False, null=False)

    def __str__(self):
        return f"[Range {self.id}] {self.value}"


class Segment(models.Model):
    value = models.CharField(
        max_length=30, unique=True, blank=False, null=False)

    def __str__(self):
        return f"[Segment {self.id}] {self.value}"


class Product(models.Model):
    sku = models.CharField(max_length=30, unique=True, blank=False, null=False)
    marketing_name = models.CharField(max_length=50, blank=False, null=False)
    end_of_production = models.DateTimeField(default=None)
    brand = models.ForeignKey(
        Brand, related_name='product', on_delete=models.DO_NOTHING)
    segment = models.ForeignKey(
        Segment, related_name='product', on_delete=models.DO_NOTHING)
    product_range = models.ForeignKey(
        Range, related_name='product', on_delete=models.DO_NOTHING)
    division = models.ForeignKey(
        Division, related_name='product', on_delete=models.DO_NOTHING)
    group = models.ForeignKey(
        Group, related_name='product', on_delete=models.DO_NOTHING)
    # base model ?

    def __str__(self) -> str:
        return f"{self.sku} ({self.id})"


class ProductType(models.Model):
    product = models.ForeignKey(
        Product, related_name='type', on_delete=models.DO_NOTHING)
    key = models.CharField(max_length=30, blank=False,
                           null=False, default="key")
    value = models.CharField(max_length=30, blank=False,
                             null=False, default="value")

    class Meta:
        unique_together = ('key', 'value', 'product')


class Week(models.Model):
    year = models.IntegerField(null=False, blank=False)
    week = models.SmallIntegerField(null=False, blank=False)

    def __str__(self) -> str:
        return f"({self.year}) {self.week}"

    class Meta:
        unique_together = ('year', 'week')


class WeeklySale(models.Model):
    year = models.IntegerField(null=False, blank=False)
    week = models.SmallIntegerField(null=False, blank=False)
    week_object = models.ForeignKey(
        Week, related_name='weeklysale', on_delete=models.DO_NOTHING, default=1)
    first_date_of_week = models.DateField(null=False, blank=False)
    site_id = models.ForeignKey(
        PointOfSale, related_name='weeklysale', on_delete=models.DO_NOTHING)
    product = models.ForeignKey(
        Product, related_name='weeklysale', on_delete=models.DO_NOTHING)
    sold_units = models.IntegerField(default=0, null=False, blank=False)
    inventory = models.IntegerField(default=0, null=False, blank=False)

    class Meta:
        unique_together = ('year', 'week', 'product', 'site_id')
