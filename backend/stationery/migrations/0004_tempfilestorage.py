# Generated by Django 5.0 on 2024-01-28 08:29

import stationery.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stationery', '0003_alter_activeorders_custom_message_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TempFileStorage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=stationery.utils.temp_file_rename)),
            ],
            options={
                'verbose_name_plural': 'Temporary Files',
                'db_table': 'stationery_temp_files',
            },
        ),
    ]