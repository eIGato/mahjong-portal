# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2017-12-17 13:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='inner_rating_place',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='inner_rating_score',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
    ]