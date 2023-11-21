# Generated by Django 4.0.4 on 2022-07-21 15:18

import administration.managers
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('views', '__first__'),
        ('store', '__first__'),
        ('locations', '0001_initial'),
        ('product', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=30)),
                ('last_name', models.CharField(blank=True, max_length=30)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('avatar', models.CharField(blank=True, max_length=250)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_dev', models.BooleanField(default=False)),
                ('otp', models.TextField(default=None, max_length=128, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
            managers=[
                ('objects', administration.managers.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='CacheBatchJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.CharField(blank=True, max_length=200)),
                ('job_id', models.CharField(blank=True, max_length=36)),
                ('query', models.CharField(blank=True, max_length=250)),
                ('started', models.DateTimeField(auto_now_add=True)),
                ('ended', models.DateTimeField()),
                ('failed', models.BooleanField(default=False)),
                ('result', models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ViewsLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='log', to=settings.AUTH_USER_MODEL)),
                ('view', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='log', to='views.view')),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_started', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_name', models.CharField(max_length=30, unique=True)),
                ('status', models.BooleanField(default=False)),
                ('accounts', models.ManyToManyField(to='store.account')),
                ('countries', models.ManyToManyField(to='locations.country')),
                ('divisions', models.ManyToManyField(to='product.division')),
                #('point_of_sales', models.ManyToManyField(to='store.pointofsale')),
                ('views', models.ManyToManyField(to='views.view')),
            ],
        ),
        migrations.CreateModel(
            name='PasswordChangeCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.PositiveIntegerField()),
                ('used', models.BooleanField(default=False)),
                ('expiration', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='password_change_code', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='roles',
            field=models.ManyToManyField(to='administration.role'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]