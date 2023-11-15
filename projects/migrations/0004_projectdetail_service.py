# Generated by Django 4.2.6 on 2023-11-06 02:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agencies', '0003_alter_businessarea_unique_together'),
        ('projects', '0003_alter_researchfunction_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectdetail',
            name='service',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='agencies.departmentalservice'),
        ),
    ]