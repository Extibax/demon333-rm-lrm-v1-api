# Generated by Django 4.0.4 on 2022-11-17 02:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0011_alter_userstatuslog_country'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userstatuslog',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='userstatuslog',
            name='last_login',
            field=models.DateTimeField(null=True),
        ),
    ]