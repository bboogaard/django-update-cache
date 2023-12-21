# Generated by Django 4.2.8 on 2023-12-20 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CacheEntry',
            fields=[
                ('cache_key', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('function', models.CharField(max_length=255)),
                ('calling_args', models.TextField(blank=True)),
                ('value', models.TextField()),
                ('expires', models.DateTimeField(null=True)),
                ('has_expired', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Cache entry',
                'verbose_name_plural': 'Cache entries',
                'managed': False,
            },
        ),
    ]