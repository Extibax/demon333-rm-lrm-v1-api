from django.db import models

# Create your models here.
from administration.models import User
from store.models import PointOfSale


class Status(models.Model):
    # coordinates
    value = models.CharField(max_length=20)
    color = models.CharField(max_length=6)  # hex value
    def __str__(self):
        return f"[Status {self.id}] {self.value}"
    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Status'

class ActionPlan(models.Model):
    # coordinates
    content = models.TextField(max_length=200)
    creation_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True)
    pos_type = models.ForeignKey(
        PointOfSale, related_name='actionplan', on_delete=models.DO_NOTHING)
    user = models.ForeignKey(
        User, related_name='actionplan', on_delete=models.DO_NOTHING)
    status = models.ForeignKey(
        Status, related_name='actionplan', on_delete=models.DO_NOTHING)
    
