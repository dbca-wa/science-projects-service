# Generated by Django 5.1 on 2024-08-18 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_user_display_first_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='publicstaffprofile',
            name='publications',
        ),
        migrations.RemoveField(
            model_name='staffprofileprojectentry',
            name='project_membership',
        ),
        migrations.RemoveField(
            model_name='staffprofileprojectentry',
            name='public_profile',
        ),
        migrations.RemoveField(
            model_name='publicstaffprofile',
            name='dbca_position_title',
        ),
        migrations.RemoveField(
            model_name='publicstaffprofile',
            name='education',
        ),
        migrations.RemoveField(
            model_name='publicstaffprofile',
            name='employment',
        ),
        migrations.RemoveField(
            model_name='publicstaffprofile',
            name='project_memberships',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='curriculum_vitae',
        ),
        migrations.AddField(
            model_name='publicstaffprofile',
            name='title',
            field=models.CharField(blank=True, choices=[('mr', 'Mr.'), ('ms', 'Ms.'), ('mrs', 'Mrs.'), ('master', 'Master'), ('dr', 'Dr.')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='publicstaffprofile',
            name='about_me',
            field=models.TextField(blank=True, help_text='Short biography or personal statement.', null=True),
        ),
        migrations.AlterField(
            model_name='publicstaffprofile',
            name='expertise',
            field=models.TextField(blank=True, help_text='Areas of expertise or specializations.', null=True),
        ),
        migrations.AlterField(
            model_name='publicstaffprofile',
            name='keyword_tags',
            field=models.TextField(blank=True, help_text='Comma-separated tags describing areas of expertise.', null=True),
        ),
        migrations.DeleteModel(
            name='AdditionalPublicationEntry',
        ),
        migrations.DeleteModel(
            name='StaffProfileProjectEntry',
        ),
    ]