from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'value', 'color')
    search_fields = ('value', 'color',)

@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'content', 'creation_date', 'due_date', 'pos_type', 'user', 'status')
    search_fields = ('content', 'creation_date', 'due_date', 'pos_type', 'user', 'status')