# Generated by Django 2.2.3 on 2019-07-28 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookmp', '0014_auto_20190727_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seller',
            name='price',
            field=models.IntegerField(null=True),
        ),
    ]
