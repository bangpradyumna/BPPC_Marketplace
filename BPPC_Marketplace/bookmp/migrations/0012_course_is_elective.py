# Generated by Django 2.2.3 on 2019-07-26 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookmp', '0011_auto_20190724_1633'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='is_elective',
            field=models.BooleanField(default=False),
        ),
    ]
