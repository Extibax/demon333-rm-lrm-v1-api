# Generated by Django 4.0.4 on 2022-10-07 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_alter_layeroneuri_uri'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layeronebatch',
            name='description',
            field=models.CharField(max_length=50),
        ),
    ]