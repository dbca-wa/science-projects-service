# Generated by Django 5.1 on 2024-08-18 20:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_rename_about_me_publicstaffprofile_about'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeywordTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name='publicstaffprofile',
            name='aucode',
            field=models.CharField(blank=True, help_text='AU code for internal use.', max_length=50, null=True),
        ),
        migrations.RemoveField(
            model_name='publicstaffprofile',
            name='keyword_tags',
        ),
        migrations.AlterField(
            model_name='publicstaffprofile',
            name='user',
            field=models.OneToOneField(help_text='Linked user account for this staff profile.', on_delete=django.db.models.deletion.CASCADE, related_name='staff_profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='publicstaffprofile',
            name='keyword_tags',
            field=models.ManyToManyField(blank=True, help_text='Tags describing areas of expertise.', related_name='staff_profiles', to='users.keywordtag'),
        ),
    ]
