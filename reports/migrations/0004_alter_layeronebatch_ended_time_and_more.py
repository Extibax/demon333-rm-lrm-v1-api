# Generated by Django 4.0.4 on 2022-10-06 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_layeronebatch_layeroneuri_monitorcpu_monitorram_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layeronebatch',
            name='ended_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='layeronebatch',
            name='started_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='layeroneprogress',
            name='ended_time',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='layeroneprogress',
            name='started_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
