# Generated by Django 4.0.4 on 2022-07-21 15:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0001_initial'),
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='weeklysale',
            name='site_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='weeklysale', to='store.pointofsale'),
        ),
        migrations.AddField(
            model_name='weeklysale',
            name='week_object',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='weeklysale', to='product.week'),
        ),
        migrations.AlterUniqueTogether(
            name='week',
            unique_together={('year', 'week')},
        ),
        migrations.AddField(
            model_name='producttype',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='type', to='product.product'),
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='product', to='product.brand'),
        ),
        migrations.AddField(
            model_name='product',
            name='division',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='product', to='product.division'),
        ),
        migrations.AddField(
            model_name='product',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='product', to='product.group'),
        ),
        migrations.AddField(
            model_name='product',
            name='product_range',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='product', to='product.range'),
        ),
        migrations.AddField(
            model_name='product',
            name='segment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='product', to='product.segment'),
        ),
        migrations.AlterUniqueTogether(
            name='weeklysale',
            unique_together={('year', 'week', 'product', 'site_id')},
        ),
        migrations.AlterUniqueTogether(
            name='producttype',
            unique_together={('key', 'value', 'product')},
        ),
    ]
