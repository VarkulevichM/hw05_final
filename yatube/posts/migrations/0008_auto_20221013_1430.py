# Generated by Django 2.2.16 on 2022-10-13 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20221013_1420'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='you_cant_on_yourself_user',
        ),
        migrations.RemoveConstraint(
            model_name='follow',
            name='You_cant_on_yourself_author',
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('author', 'user'), name='you_cant_on_yourself'),
        ),
    ]
