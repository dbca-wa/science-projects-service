# Generated by Django 5.1.1 on 2024-09-19 05:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_alter_user_display_first_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='educationentry',
            name='qualification_field',
        ),
        migrations.RemoveField(
            model_name='educationentry',
            name='qualification_kind',
        ),
        migrations.RemoveField(
            model_name='educationentry',
            name='with_honours',
        ),
    ]