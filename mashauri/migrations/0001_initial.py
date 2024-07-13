# Generated by Django 5.0.6 on 2024-07-09 23:55

import django.db.models.deletion
import mashauri.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('username', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(blank=True, default='', max_length=50)),
                ('first_name', models.CharField(blank=True, default='', max_length=50)),
                ('last_name', models.CharField(blank=True, default='', max_length=50)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_superuser', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('MSP', 'MSP'), ('FDP', 'FDP'), ('ENTERPRISE CONNECTIVITY', 'ENTERPRISE CONNECTIVITY'), ('ENTERPRISE_PROJECT', 'ENTERPRISE_PROJECT'), ('SUPPORT', 'SUPPORT'), ('ROLLOUT_PARTNER', 'ROLLOUT_PARTNER')], max_length=50)),
                ('msp_category', models.CharField(choices=[('None', 'None'), ('Egypro', 'Egypro'), ('Camusat', 'Camusat'), ('Adrian', 'Adrian'), ('Kinde', 'Kinde'), ('Fireside', 'Fireside'), ('Soliton', 'Soliton')], default='None', max_length=50, null=True)),
                ('fdp_category', models.CharField(choices=[('None', 'None'), ('Fireside', 'Fireside'), ('Broadcom', 'Broadcom'), ('Optimax', 'Optimax'), ('BTN', 'BTN'), ('Com21', 'Com21')], default='None', max_length=50, null=True)),
                ('rp_category', models.CharField(choices=[('None', 'None'), ('Fireside', 'Fireside'), ('Broadcom', 'Broadcom'), ('Optimax', 'Optimax'), ('BTN', 'BTN'), ('Com21', 'Com21')], default='None', max_length=50, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'mashauri_users',
            },
            managers=[
                ('objects', mashauri.models.CustomUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Dispatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('building_name', models.CharField(max_length=50)),
                ('building_id', models.CharField(blank=True, max_length=50, null=True)),
                ('msp', models.CharField(choices=[('Egypro', 'Egypro'), ('Camusat', 'Camusat'), ('Adrian', 'Adrian'), ('Kinde', 'Kinde'), ('Fireside', 'Fireside'), ('Soliton', 'Soliton')], max_length=50)),
                ('fdp', models.CharField(choices=[('Fireside', 'Fireside'), ('Broadcom', 'Broadcom'), ('Optimax', 'Optimax'), ('BTN', 'BTN'), ('Com21', 'Com21')], max_length=50)),
                ('rp', models.CharField(choices=[('Fireside', 'Fireside'), ('Broadcom', 'Broadcom'), ('Optimax', 'Optimax'), ('BTN', 'BTN'), ('Com21', 'Com21')], max_length=50)),
                ('status', models.CharField(choices=[('Hold', 'Hold'), ('Progress', 'Progress'), ('Closed', 'Closed')], default='Progress', max_length=50)),
                ('escalation_type', models.CharField(choices=[('Proactive', 'Proactive'), ('Reactive', 'Reactive'), ('OTB', 'OTB'), ('Support', 'Support'), ('Optimization', 'Optimization')], max_length=50)),
                ('comments', models.TextField(blank=True, null=True)),
                ('coordinates', models.CharField(blank=True, help_text='Latitude and Longitude tuple as "latitude,longitude"', max_length=50, null=True)),
                ('client_id', models.CharField(blank=True, max_length=50, null=True)),
                ('client_name', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sla_timer', models.DateTimeField(blank=True, null=True)),
                ('dispatch_image', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Dispatches',
                'db_table': 'mashauri_dispatches',
            },
        ),
        migrations.CreateModel(
            name='SLA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('dispatch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mashauri.dispatch')),
            ],
            options={
                'verbose_name': 'SLA',
                'verbose_name_plural': 'SLAs',
                'db_table': 'mashauri_SLAs',
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Open', 'Open'), ('In Progress', 'In Progress'), ('Closed', 'Closed')], max_length=50)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('dispatch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mashauri.dispatch')),
            ],
            options={
                'db_table': 'mashauri_tickets',
            },
        ),
    ]
