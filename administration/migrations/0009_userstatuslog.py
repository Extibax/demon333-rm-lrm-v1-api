# Generated by Django 4.0.4 on 2022-11-15 22:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0008_alter_teamleader_team_leader_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('status', models.CharField(max_length=100)),
                ('last_login', models.CharField(blank=True, max_length=30)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_log', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]