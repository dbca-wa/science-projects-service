# Generated by Django 5.1.6 on 2025-02-24 01:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_alter_publicstaffprofile_employee_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicstaffprofile',
            name='custom_title',
            field=models.CharField(blank=True, help_text='Custom title or position name.', max_length=50, null=True),
        ),
    ]
