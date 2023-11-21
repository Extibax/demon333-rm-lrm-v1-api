from django.contrib import admin
from .models import View
# Register your models here.


@admin.register(View)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description',
                    'group1', 'division', 'country')
    search_fields = ('name',)
