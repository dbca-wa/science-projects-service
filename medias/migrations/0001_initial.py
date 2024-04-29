# Generated by Django 5.0.4 on 2024-04-23 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AECEndorsementPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='aec_endorsements/')),
            ],
            options={
                'verbose_name': 'AEC PDF',
                'verbose_name_plural': 'AEC PDFs',
            },
        ),
        migrations.CreateModel(
            name='AgencyImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.ImageField(upload_to='agencies/')),
            ],
            options={
                'verbose_name': 'Agency Image',
                'verbose_name_plural': 'Agency Images',
            },
        ),
        migrations.CreateModel(
            name='AnnualReportMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.ImageField(blank=True, null=True, upload_to='annual_reports/images/')),
                ('kind', models.CharField(choices=[('cover', 'Cover'), ('rear_cover', 'Rear Cover'), ('sdchart', 'Service Delivery Chart'), ('service_delivery', 'Service Delivery'), ('research', 'Research'), ('partnerships', 'Partnerships'), ('collaborations', 'Collaborations'), ('student_projects', 'Student Projects'), ('publications', 'Publications')], max_length=140)),
            ],
            options={
                'verbose_name': 'Annual Report Image',
                'verbose_name_plural': 'Annual Report Images',
            },
        ),
        migrations.CreateModel(
            name='AnnualReportPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='annual_reports/pdfs/')),
            ],
            options={
                'verbose_name': 'Annual Report PDF',
                'verbose_name_plural': 'Annual Report PDFs',
            },
        ),
        migrations.CreateModel(
            name='BusinessAreaPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.ImageField(blank=True, null=True, upload_to='business_areas/')),
            ],
            options={
                'verbose_name': 'Business Area Image',
                'verbose_name_plural': 'Business Area Images',
            },
        ),
        migrations.CreateModel(
            name='ProjectDocumentPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='project_documents/')),
            ],
            options={
                'verbose_name': 'Project Document PDF',
                'verbose_name_plural': 'Project Document PDFs',
            },
        ),
        migrations.CreateModel(
            name='ProjectPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.ImageField(blank=True, null=True, upload_to='projects/')),
            ],
            options={
                'verbose_name': 'Project Image',
                'verbose_name_plural': 'Project Images',
            },
        ),
        migrations.CreateModel(
            name='ProjectPlanMethodologyPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.ImageField(blank=True, null=True, upload_to='methodology_images/')),
            ],
            options={
                'verbose_name': 'Methodology Image File',
                'verbose_name_plural': 'Methodology Image Files',
            },
        ),
        migrations.CreateModel(
            name='UserAvatar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.ImageField(blank=True, null=True, upload_to='user_avatars/')),
            ],
            options={
                'verbose_name': 'User Avatar Image',
                'verbose_name_plural': 'User Avatar Images',
            },
        ),
    ]
