# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2017-12-24 06:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='is_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
