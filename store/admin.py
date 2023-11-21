from django.contrib import admin
from .models import Segment, PointOfSaleType, Account, PointOfSale,CustomAccountMapping
# Register your models here.


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('value',)


@admin.register(PointOfSaleType)
class PointOfSaleTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'value')
    search_fields = ('value',)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(CustomAccountMapping)
class CustomAccountMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'original',"custom","store_like")
    search_fields = ('original',"custom")
    list_editable=("store_like",)



@admin.register(PointOfSale)
class PointOfSaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'site_id', 'gscn_site_name',
                    'pos_type', 'city', 'segment', 'account', 'status')
    search_fields = ('site_id', 'gscn_site_name', 'pos_type',
                     'city', 'segment', 'account', 'status')
