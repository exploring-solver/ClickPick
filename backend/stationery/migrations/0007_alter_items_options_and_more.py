# Generated by Django 5.0 on 2024-03-23 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stationery', '0006_tempfilestorage'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='items',
            options={'verbose_name_plural': 'All Items'},
        ),
        migrations.AddField(
            model_name='activeprintouts',
            name='print_on_one_side',
            field=models.BooleanField(default=True),
        ),
    ]
