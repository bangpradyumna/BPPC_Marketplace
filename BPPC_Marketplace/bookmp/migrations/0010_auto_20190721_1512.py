# Generated by Django 2.2.3 on 2019-07-21 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookmp', '0009_auto_20190719_1414'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='single_branch',
            field=models.CharField(choices=[('A1', 'B.E. Chemical'), ('A2', 'B.E. Civil'), ('A7', 'B.E. Computer Science'), ('A3', 'B.E. Electrical & Electronics'), ('A8', 'B.E. Electronics & Instrumentation'), ('A4', 'B.E. Mechanical'), ('AB', 'B.E. Manufacturing'), ('A5', 'B.Pharm.')], max_length=100, null=True),
        ),
    ]