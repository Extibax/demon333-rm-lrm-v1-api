# Generated by Django 4.0.4 on 2022-10-06 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_monitorcpu_env_monitorram_env'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layeroneuri',
            name='uri',
            field=models.CharField(max_length=150, unique=True),
        ),
    ]
