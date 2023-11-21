from django.contrib import admin
from .models import Division, Group, Brand, Range, Segment, Product, ProductType, WeeklySale, Week
# Register your models here.


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('value',)
    #list_editable = ('slug', 'imageURL')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('value',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('value',)


@admin.register(Range)
class RangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('value',)


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('value',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'marketing_name', 'brand',
                    'segment', 'product_range', 'division', 'group')
    search_fields = ('sku', 'marketing_name', 'brand',
                     'segment', 'product_range', 'division', 'group',)


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'key', 'value')
    search_fields = ('product', 'key', 'value',)


@admin.register(WeeklySale)
class WeeklySaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'year', 'week', 'first_date_of_week',
                    'site_id', 'product', 'sold_units', 'inventory')
    search_fields = ('year', 'week', 'first_date_of_week',
                     'site_id', 'product', 'sold_units', 'inventory',)


@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ('id', 'year', 'week')
    search_fields = ('year', 'week')
