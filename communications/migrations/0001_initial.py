# Generated by Django 5.0.2 on 2024-03-01 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChatRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Chat Room',
                'verbose_name_plural': 'Chat Rooms',
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('text', models.CharField(max_length=1500)),
                ('ip_address', models.CharField(blank=True, max_length=45, null=True)),
                ('is_public', models.BooleanField(default=True)),
                ('is_removed', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
            },
        ),
        migrations.CreateModel(
            name='DirectMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('text', models.TextField()),
                ('ip_address', models.CharField(blank=True, max_length=45, null=True)),
                ('is_public', models.BooleanField(default=True)),
                ('is_removed', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Direct Message',
                'verbose_name_plural': 'Direct Messages',
            },
        ),
        migrations.CreateModel(
            name='Reaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reaction', models.CharField(choices=[('thumbup', 'Thumbs Up'), ('thumbdown', 'Thumbs Down'), ('heart', 'Heart'), ('brokenheart', 'Broken Heart'), ('hundred', 'Hundred'), ('confused', 'Confused'), ('funny', 'Funny'), ('surprised', 'Surprised')], max_length=30)),
            ],
            options={
                'verbose_name': 'Reaction',
                'verbose_name_plural': 'Reactions',
            },
        ),
    ]
