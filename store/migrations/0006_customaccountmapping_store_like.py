# Generated by Django 4.0.4 on 2022-09-21 01:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_alter_customaccountmapping_custom_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customaccountmapping',
            name='store_like',
            field=models.CharField(default='CATCO', max_length=15),
            preserve_default=False,
        ),
    ]
