# Generated by Django 4.0.4 on 2022-11-15 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0009_remove_layeroneprogress_batch_layeronelot_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportsFrames',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report', models.TextField(max_length=100)),
                ('token', models.TextField(max_length=255)),
            ],
        ),
    ]