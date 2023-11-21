from django.db import models
from locations.models import Country

from product.models import Division
#from administration.models import User
# Create your models here.


class View(models.Model):
    name = models.CharField(max_length=30, blank=False,
                            null=False, unique=True)
    description = models.CharField(max_length=100, default="")
    group1 = models.CharField(
        max_length=150, blank=True, null=True, default="")
    division = models.ForeignKey(
        Division, related_name='view', on_delete=models.CASCADE, blank=True, null=True)
    country = models.ForeignKey(
        Country, related_name='view', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"[View {self.id}] {self.name}"
