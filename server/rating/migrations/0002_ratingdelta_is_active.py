# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2017-12-16 18:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rating', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ratingdelta',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]