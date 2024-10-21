# Generated by Django 5.1.2 on 2024-10-17 00:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminoptions', '0004_admintask'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='admintask',
            options={'verbose_name': 'Admin Task', 'verbose_name_plural': 'Admin Tasks'},
        ),
        migrations.AddField(
            model_name='admintask',
            name='end_date',
            field=models.DateTimeField(blank=True, help_text='The date the task was completed', null=True),
        ),
        migrations.AddField(
            model_name='admintask',
            name='notes',
            field=models.TextField(blank=True, help_text='Any additional notes for the task', null=True),
        ),
        migrations.AddField(
            model_name='admintask',
            name='reason',
            field=models.TextField(blank=True, help_text='The reasoning for the task', null=True),
        ),
        migrations.AddField(
            model_name='admintask',
            name='start_date',
            field=models.DateTimeField(blank=True, help_text='The date the task was initiated', null=True),
        ),
        migrations.AlterField(
            model_name='admintask',
            name='secondary_users',
            field=models.JSONField(blank=True, help_text='An array of user pks to merge or set caretaker (array of 1)', null=True),
        ),
        migrations.AlterField(
            model_name='admintask',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('fulfilled', 'Fulfilled'), ('rejected', 'Rejected')], default='pending', max_length=50),
        ),
        migrations.CreateModel(
            name='Caretaker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('start_date', models.DateTimeField(blank=True, help_text='The date the caretaker request was initiated', null=True)),
                ('end_date', models.DateTimeField(blank=True, help_text='The date the caretaker request was completed', null=True)),
                ('reason', models.TextField(blank=True, help_text='The reasoning for the caretaker request', null=True)),
                ('notes', models.TextField(blank=True, help_text='Any additional notes for the caretaker request', null=True)),
                ('caretaker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='caretaker_for', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='caretaker', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Caretaker',
                'verbose_name_plural': 'Caretakers',
            },
        ),
    ]
