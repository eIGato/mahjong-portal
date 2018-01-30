# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-28 12:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('online', '0004_tournamentstatus_end_break_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournamentgame',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[[0, 'New'], [1, 'Started'], [2, 'Failed to start'], [3, 'Finished']], default=0),
        ),
    ]