# Generated by Django 2.2.19 on 2022-04-02 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_auto_20220402_2346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(max_length=200, null=True, unique=True),
        ),
    ]
