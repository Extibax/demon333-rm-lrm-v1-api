# Generated by Django 4.0.4 on 2022-11-01 16:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0003_country_latitude_country_longitude'),
        ('administration', '0005_authorizedemaildomain_company_department_jobposition_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='viewslog',
            name='country_id',
        ),
        migrations.AddField(
            model_name='viewslog',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='log', to='locations.country'),
        ),
    ]
