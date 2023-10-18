# Generated by Django 4.2.5 on 2023-10-06 02:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("agencies", "0002_initial"),
        ("documents", "0002_initial"),
        ("medias", "0001_initial"),
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="useravatar",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="avatar",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="projectphoto",
            name="project",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="image",
                to="projects.project",
            ),
        ),
        migrations.AddField(
            model_name="projectphoto",
            name="uploader",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="project_photos_uploaded",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="projectdocumentpdf",
            name="document",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="pdf",
                to="documents.projectdocument",
            ),
        ),
        migrations.AddField(
            model_name="projectdocumentpdf",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="pdfs",
                to="projects.project",
            ),
        ),
        migrations.AddField(
            model_name="businessareaphoto",
            name="business_area",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="image",
                to="agencies.businessarea",
            ),
        ),
        migrations.AddField(
            model_name="businessareaphoto",
            name="uploader",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="business_area_photos_uploaded",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="annualreportmedia",
            name="report",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="media",
                to="documents.annualreport",
            ),
        ),
        migrations.AddField(
            model_name="annualreportmedia",
            name="uploader",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="annual_report_media_uploaded",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="agencyimage",
            name="agency",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="image",
                to="agencies.agency",
            ),
        ),
        migrations.AddConstraint(
            model_name="annualreportmedia",
            constraint=models.UniqueConstraint(
                fields=("kind", "report"), name="unique_media_per_kind_per_year"
            ),
        ),
    ]
