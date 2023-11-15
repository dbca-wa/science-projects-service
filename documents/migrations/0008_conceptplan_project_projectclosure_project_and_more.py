# Generated by Django 4.2.6 on 2023-11-15 01:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_projectdetail_service'),
        ('documents', '0007_progressreport_project_studentreport_project_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conceptplan',
            name='project',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='concept_plan', to='projects.project'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='projectclosure',
            name='project',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='closure', to='projects.project'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='projectplan',
            name='project',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='project_plan', to='projects.project'),
            preserve_default=False,
        ),
    ]
