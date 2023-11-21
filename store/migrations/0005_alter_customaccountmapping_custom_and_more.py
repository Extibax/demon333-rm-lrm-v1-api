# Generated by Django 4.0.4 on 2022-09-21 01:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_customaccountmapping'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customaccountmapping',
            name='custom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='custom_mapping', to='store.account'),
        ),
        migrations.AlterField(
            model_name='customaccountmapping',
            name='original',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='original_mapping', to='store.account'),
        ),
    ]
