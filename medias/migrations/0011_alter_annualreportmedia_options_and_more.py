# Generated by Django 4.2.6 on 2023-11-02 06:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0002_initial'),
        ('medias', '0010_remove_businessareaphoto_old_file_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='annualreportmedia',
            options={'verbose_name': 'Annual Report Image', 'verbose_name_plural': 'Annual Report Images'},
        ),
        migrations.AlterField(
            model_name='annualreportmedia',
            name='file',
            field=models.ImageField(blank=True, null=True, upload_to='annual_reports/images/'),
        ),
        migrations.AlterField(
            model_name='annualreportmedia',
            name='kind',
            field=models.CharField(choices=[('cover', 'Cover'), ('rear_cover', 'Rear Cover'), ('sdchart', 'Service Delivery Chart'), ('service_delivery', 'Service Delivery'), ('research', 'Research'), ('partnerships', 'Partnerships'), ('collaborations', 'Collaborations'), ('student_projects', 'Student Projects'), ('publications', 'Publications')], max_length=140),
        ),
        migrations.CreateModel(
            name='AnnualReportPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('old_file', models.URLField(blank=True, null=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='annual_reports/pdfs/')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annual_report_pdf_generated', to=settings.AUTH_USER_MODEL)),
                ('report', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pdf', to='documents.annualreport')),
            ],
            options={
                'verbose_name': 'Annual Report PDF',
                'verbose_name_plural': 'Annual Report PDFs',
            },
        ),
    ]
