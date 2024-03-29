# Generated by Django 2.2.3 on 2019-07-09 04:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bits_id', models.CharField(max_length=13)),
                ('year', models.IntegerField(choices=[('1', '1st Year'), ('2', '2nd Year'), ('3', '3rd Year'), ('4', '4th Year'), ('5', '5th Year')])),
                ('is_dual_degree', models.BooleanField(default=False)),
                ('single_branch', models.CharField(choices=[('CHEMENGG', 'B.E. Chemical'), ('CIVILENGG', 'B.E. Civil'), ('CS', 'B.E. Computer Science'), ('EEE', 'B.E. Electrical & Electronics'), ('ENI', 'B.E. Electronics & Instrumentation'), ('MECHENGG', 'B.E. Mechanical'), ('MANUENGG', 'B.E. Manufacturing'), ('BPHARMA', 'B.Pharm.')], max_length=100)),
                ('dual_branch', models.CharField(choices=[('BIO', 'M.Sc. Biological Sciences'), ('CHEM', 'M.Sc. Chemistry'), ('ECO', 'M.Sc. Economics'), ('MATHS', 'M.Sc. Mathematics'), ('PHY', 'M.Sc. Physics')], max_length=100, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
