# Generated by Django 4.2.6 on 2023-11-30 03:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('agencies', '0002_initial'),
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercontact',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contact', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='branchcontact',
            name='address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contacts.address'),
        ),
        migrations.AddField(
            model_name='branchcontact',
            name='branch',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contact', to='agencies.branch'),
        ),
        migrations.AddField(
            model_name='agencycontact',
            name='address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contacts.address'),
        ),
        migrations.AddField(
            model_name='agencycontact',
            name='agency',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contact', to='agencies.agency'),
        ),
        migrations.AddField(
            model_name='address',
            name='agency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='address', to='agencies.agency'),
        ),
        migrations.AddField(
            model_name='address',
            name='branch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='address', to='agencies.branch'),
        ),
    ]
