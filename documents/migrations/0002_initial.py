# Generated by Django 5.0.6 on 2024-05-11 03:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('documents', '0001_initial'),
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='annualreport',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annualreport',
            name='modifier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modified_reports', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conceptplan',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='concept_plan', to='projects.project'),
        ),
        migrations.AddField(
            model_name='progressreport',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_reports', to='projects.project'),
        ),
        migrations.AddField(
            model_name='progressreport',
            name='report',
            field=models.ForeignKey(help_text='The annual report publishing this Report', on_delete=django.db.models.deletion.CASCADE, to='documents.annualreport'),
        ),
        migrations.AddField(
            model_name='projectclosure',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='closure', to='projects.project'),
        ),
        migrations.AddField(
            model_name='projectdocument',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='projectdocument',
            name='modifier',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='projectdocument',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='projects.project'),
        ),
        migrations.AddField(
            model_name='projectclosure',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_closure_details', to='documents.projectdocument'),
        ),
        migrations.AddField(
            model_name='progressreport',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_report_details', to='documents.projectdocument'),
        ),
        migrations.AddField(
            model_name='conceptplan',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='concept_plan_details', to='documents.projectdocument'),
        ),
        migrations.AddField(
            model_name='projectplan',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_plan_details', to='documents.projectdocument'),
        ),
        migrations.AddField(
            model_name='projectplan',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_plan', to='projects.project'),
        ),
        migrations.AddField(
            model_name='endorsement',
            name='project_plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='endorsements', to='documents.projectplan'),
        ),
        migrations.AddField(
            model_name='publication',
            name='internal_authors',
            field=models.ManyToManyField(related_name='publications', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='studentreport',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_report_details', to='documents.projectdocument'),
        ),
        migrations.AddField(
            model_name='studentreport',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_reports', to='projects.project'),
        ),
        migrations.AddField(
            model_name='studentreport',
            name='report',
            field=models.ForeignKey(blank=True, help_text='The annual report publishing this StudentReport', null=True, on_delete=django.db.models.deletion.SET_NULL, to='documents.annualreport'),
        ),
        migrations.AlterUniqueTogether(
            name='progressreport',
            unique_together={('report', 'project')},
        ),
        migrations.AlterUniqueTogether(
            name='studentreport',
            unique_together={('report', 'project')},
        ),
    ]
