from email.policy import default
from django.db import models

from product.models import Product, Week
from store.models import PointOfSale
# Create your models here.


class Flooring(models.Model):
    week = models.ForeignKey(
        Week, related_name='flooring', on_delete=models.DO_NOTHING)
    product = models.ForeignKey(
        Product, related_name='flooring', on_delete=models.DO_NOTHING)
    point_of_sale = models.ForeignKey(
        PointOfSale, related_name='flooring', on_delete=models.DO_NOTHING)
    target = models.IntegerField(default=0)

    class Meta:
        unique_together = ('week', 'product', 'point_of_sale')
#region cache-layer-1
class LayerOneURI(models.Model):
    uri = models.CharField(max_length=150,unique=True)

class LayerOneBatch(models.Model):
    dynamo_id = models.IntegerField(default=0)
    description  = models.CharField(max_length=50)
    uri = models.ForeignKey(LayerOneURI, related_name='layer_one_uri', on_delete=models.DO_NOTHING)
    started_time = models.DateTimeField(auto_now_add=True)
    ended_time = models.DateTimeField(auto_now_add=False, null=True)
    population = models.IntegerField(default=0)
    progress = models.IntegerField(default=0)

class LayerOneLot(models.Model):
    batch =  models.ForeignKey(
        LayerOneBatch, related_name='layer_one_batch', on_delete=models.DO_NOTHING)
    speed = models.DecimalField(decimal_places=2,max_digits=5)
    started_time = models.DateTimeField(auto_now_add=True)
    ended_time =  models.DateTimeField(auto_now_add=False, null=True)
    progress = models.IntegerField()
    size = models.PositiveSmallIntegerField()
class LayerOneProgress(models.Model):
    lot = models.ForeignKey(LayerOneLot,related_name = "layer_one_lot", on_delete=models.DO_NOTHING)
    started_time = models.DateTimeField(auto_now_add=True)
    ended_time =  models.DateTimeField(auto_now_add=False, null=True)
    status_code = models.IntegerField()
    item = models.CharField(max_length=250)
    redis_key = models.CharField(max_length=250)
    
class MonitorRAM(models.Model):
    log_time = models.DateTimeField(auto_now_add=True)
    value = models.DecimalField(decimal_places=2,max_digits=3)
    gb = models.DecimalField(decimal_places=2,max_digits=4)
    ip = models.CharField(max_length=16)
    env =models.CharField(max_length=5,default="local")
class MonitorCPU(models.Model):
    log_time = models.DateTimeField(auto_now_add=True)
    value = models.DecimalField(decimal_places=2,max_digits=3)
    ip = models.CharField(max_length=16)
    env =models.CharField(max_length=5,default="local")

class PowerBI(models.Model):
    report = models.TextField(max_length=100)
    token = models.TextField(max_length=255)

#endregion cache-layer-1