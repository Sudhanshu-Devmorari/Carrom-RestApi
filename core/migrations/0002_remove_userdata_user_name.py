# Generated by Django 4.2 on 2023-04-07 06:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userdata',
            name='user_name',
        ),
    ]
