# Generated by Django 5.0 on 2023-12-06 13:01

import django.contrib.postgres.fields
import django.db.models.deletion
import projects.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('agencies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('old_output_program_id', models.BigIntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Base Project Detail',
                'verbose_name_plural': 'Base Project Details',
            },
        ),
        migrations.CreateModel(
            name='ProjectMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_leader', models.BooleanField(default=False)),
                ('role', models.CharField(choices=[('supervising', 'Supervising Scientist'), ('research', 'Research Scientist'), ('technical', 'Technical Officer'), ('externalcol', 'External Collaborator'), ('academicsuper', 'Academic Supervisor'), ('student', 'Supervised Student'), ('externalpeer', 'External Peer'), ('consulted', 'Consulted Peer'), ('group', 'Involved Group')], max_length=50)),
                ('time_allocation', models.FloatField(blank=True, default=0, help_text='Indicative time allocation as a fraction of a Full Time Equivalent (210 person-days). Values between 0 and 1. Fill in estimated allocation for the next 12 months.', null=True, verbose_name='Time allocation (0 to 1 FTE)')),
                ('position', models.IntegerField(blank=True, default=100, help_text='The lowest position number comes first in the team members list. Ignore to keep alphabetical order, increase to shift member towards the end of the list, decrease to promote member to beginning of the list.', null=True, verbose_name='List position')),
                ('short_code', models.CharField(blank=True, help_text="Cost code for this project membership's salary. Allocated by divisional admin.", max_length=500, null=True, verbose_name='Short code')),
                ('comments', models.TextField(blank=True, help_text='Any comments clarifying the project membership.', null=True)),
                ('old_id', models.BigIntegerField()),
            ],
            options={
                'verbose_name': 'Project Member',
                'verbose_name_plural': 'Project Members',
            },
        ),
        migrations.CreateModel(
            name='ResearchFunction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('association', models.TextField(blank=True, help_text="The research function's association with departmental programs/divisions.", null=True)),
                ('is_active', models.BooleanField(default=False, help_text='Whether this research function has been deprecated or not.')),
                ('old_id', models.BigIntegerField()),
            ],
            options={
                'verbose_name': 'Research Function',
                'verbose_name_plural': 'Research Functions',
            },
        ),
        migrations.CreateModel(
            name='StudentProjectDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(blank=True, choices=[('pd', 'Post-Doc'), ('phd', 'PhD'), ('msc', 'MSc'), ('honours', 'BSc Honours'), ('fourth_year', 'Fourth Year'), ('third_year', 'Third Year'), ('undergrad', 'Undergradate')], default='phd', help_text='The academic qualification achieved through this project.', max_length=50, null=True)),
                ('organisation', models.TextField(blank=True, help_text='The full name of the academic organisation.', null=True, verbose_name='Academic Organisation')),
                ('old_id', models.BigIntegerField()),
            ],
            options={
                'verbose_name': 'Student Project Detail',
                'verbose_name_plural': 'Student Project Details',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('old_id', models.BigIntegerField()),
                ('kind', models.CharField(blank=True, choices=[('science', 'Science'), ('student', 'Student'), ('external', 'External'), ('core_function', 'Core Function')], help_text="The project type determines the approval and                     documentation requirements during the project's                     life span. Choose wisely - you will not be able                     to change the project type later.                     If you get it wrong, create a new project of the                     correct type and tell admins to delete the duplicate                     project of the incorrect type.", null=True)),
                ('status', models.CharField(choices=[('new', 'New'), ('pending', 'Pending Project Plan'), ('active', 'Active (Approved)'), ('updating', 'Update Requested'), ('closure_requested', 'Closure Requested'), ('closing', 'Closure Pending Final Update'), ('final_update', 'Final Update Requested'), ('completed', 'Completed and Closed'), ('terminated', 'Terminated and Closed'), ('suspended', 'Suspended')], default='new', max_length=50)),
                ('year', models.PositiveIntegerField(default=2023, help_text='The project year with four digits, e.g. 2014')),
                ('number', models.PositiveIntegerField(default=projects.models.get_next_available_number_for_year, help_text='The running project number within the project year.')),
                ('title', models.CharField(max_length=500, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('tagline', models.CharField(blank=True, max_length=500, null=True)),
                ('keywords', models.CharField(blank=True, max_length=500, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('business_area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='agencies.businessarea')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExternalProjectDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collaboration_with', models.CharField(default='NO COLLABORATOR SET', max_length=1500)),
                ('budget', models.CharField(blank=True, max_length=1000, null=True)),
                ('description', models.CharField(blank=True, max_length=10000, null=True)),
                ('aims', models.CharField(blank=True, max_length=5000, null=True)),
                ('old_id', models.BigIntegerField()),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='external_project_info', to='projects.project')),
            ],
            options={
                'verbose_name': 'External Project Detail',
                'verbose_name_plural': 'External Project Details',
            },
        ),
        migrations.CreateModel(
            name='ProjectArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('areas', django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), default=list, size=None)),
                ('project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='area', to='projects.project')),
            ],
            options={
                'verbose_name': 'Project Area',
                'verbose_name_plural': 'Project Areas',
            },
        ),
    ]
