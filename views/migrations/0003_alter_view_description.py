# Generated by Django 4.0.4 on 2022-11-02 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('views', '0002_view_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='view',
            name='description',
            field=models.CharField(default='', max_length=100),
        ),
    ]