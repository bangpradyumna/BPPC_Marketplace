# Generated by Django 2.2.3 on 2019-07-31 16:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookmp', '0016_auto_20190728_1828'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='phone',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AddField(
            model_name='seller',
            name='times_viewed',
            field=models.IntegerField(null=True),
        ),
    ]
